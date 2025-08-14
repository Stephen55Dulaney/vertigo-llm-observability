"""
Authentication blueprint for the Vertigo Debug Toolkit.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, escape
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from wtforms import ValidationError
from datetime import datetime
from app import db
from app.models import User
from app.utils.validators import InputValidator

from . import auth_bp

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        try:
            email = InputValidator.validate_email(request.form.get('email', '').strip())
            password = request.form.get('password', '')
            remember_me = request.form.get('remember_me') == 'on'
        except ValidationError as e:
            flash(f'Invalid input: {str(e)}', 'error')
            return redirect(url_for('auth.login'))
        
        # Use enhanced authentication service
        from app.services.auth_service import auth_service
        from app.services.security_monitor import security_monitor
        
        # Find user for logging (even if authentication fails)
        user = User.query.filter_by(email=email).first()
        username = user.username if user else email
        
        # Authenticate with security monitoring
        success, authenticated_user, error_message = auth_service.authenticate_user(
            username, password, remember_me
        )
        
        if not success:
            # Record failed login attempt
            security_monitor.record_login_attempt(
                username=username,
                success=False,
                failure_reason=error_message or "invalid_credentials"
            )
            
            flash(error_message or 'Invalid email or password', 'error')
            return redirect(url_for('auth.login'))
        
        # Record successful login
        security_monitor.record_login_attempt(
            username=authenticated_user.username,
            success=True
        )
        
        login_user(authenticated_user, remember=remember_me)
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard.index')
        
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile."""
    if request.method == 'POST':
        try:
            username = InputValidator.validate_username(request.form.get('username', '').strip())
            email = InputValidator.validate_email(request.form.get('email', '').strip())
        except ValidationError as e:
            flash(f'Invalid input: {str(e)}', 'error')
            return redirect(url_for('auth.edit_profile'))
        
            # Check if username/email already exists
            existing_user = User.query.filter(
                User.username == username,
                User.id != current_user.id
            ).first()
            if existing_user:
                flash('Username already taken', 'error')
                return redirect(url_for('auth.edit_profile'))
            
            existing_email = User.query.filter(
                User.email == email,
                User.id != current_user.id
            ).first()
            if existing_email:
                flash('Email already registered', 'error')
                return redirect(url_for('auth.edit_profile'))
        except Exception as e:
            flash('Error processing profile update', 'error')
            return redirect(url_for('auth.edit_profile'))
        
        current_user.username = username
        current_user.email = email
        db.session.commit()
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html', user=current_user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password."""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('auth.change_password'))
        
        # Validate new password strength
        try:
            temp_user = User(email='temp', username='temp')
            temp_user.set_password(new_password)  # This will validate the password
        except ValueError as e:
            flash('Password must be at least 12 characters with uppercase, lowercase, number, and special character', 'error')
            return redirect(url_for('auth.change_password'))
        
        try:
            current_user.set_password(new_password)
            db.session.commit()
        except ValueError as e:
            flash('Password validation failed', 'error')
            return redirect(url_for('auth.change_password'))
        
        flash('Password changed successfully', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')

@auth_bp.route('/admin/users')
@login_required
def admin_users():
    """Admin page to manage users."""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    users = User.query.all()
    return render_template('auth/admin_users.html', users=users)

@auth_bp.route('/admin/users/<int:user_id>/toggle')
@login_required
def toggle_user_status(user_id):
    """Toggle user active status (admin only)."""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot deactivate your own account', 'error')
        return redirect(url_for('auth.admin_users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}', 'success')
    return redirect(url_for('auth.admin_users')) 