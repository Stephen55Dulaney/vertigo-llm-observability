"""
WebSocket Service for Real-Time Updates
Advanced WebSocket implementation with room-based messaging, authentication, and tenant isolation.
"""

import os
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
from flask import current_app, g
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_login import current_user

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types."""
    SYSTEM_STATUS = "system_status"
    PERFORMANCE_UPDATE = "performance_update"
    CACHE_STATS = "cache_stats"
    ANALYTICS_UPDATE = "analytics_update"
    ALERT_NOTIFICATION = "alert_notification"
    TENANT_UPDATE = "tenant_update"
    USER_ACTIVITY = "user_activity"
    DASHBOARD_REFRESH = "dashboard_refresh"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class RoomType(Enum):
    """WebSocket room types."""
    GLOBAL = "global"
    TENANT = "tenant"
    USER = "user"
    ADMIN = "admin"
    PERFORMANCE = "performance"
    ANALYTICS = "analytics"
    ALERTS = "alerts"


@dataclass
class WebSocketConnection:
    """WebSocket connection metadata."""
    id: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    rooms: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    type: MessageType
    data: Dict[str, Any]
    room: Optional[str] = None
    target_user: Optional[str] = None
    target_tenant: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    priority: str = "normal"  # low, normal, high, critical
    metadata: Dict[str, Any] = field(default_factory=dict)


class WebSocketService:
    """Real-time WebSocket service with room-based messaging."""
    
    def __init__(self, socketio: SocketIO):
        """Initialize WebSocket service."""
        self.socketio = socketio
        self.connections: Dict[str, WebSocketConnection] = {}
        self.rooms: Dict[str, Set[str]] = {}
        self.message_queue: List[WebSocketMessage] = []
        self.queue_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        # Performance tracking
        self.message_stats = {
            'sent': 0,
            'received': 0,
            'errors': 0,
            'connections_total': 0,
            'connections_active': 0
        }
        
        # Heartbeat monitoring
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 90   # seconds
        self.heartbeat_thread = None
        self.heartbeat_active = False
        
        # Register event handlers
        self._register_handlers()
        
        logger.info("WebSocketService initialized")
    
    def start_heartbeat_monitoring(self) -> None:
        """Start heartbeat monitoring thread."""
        if self.heartbeat_active:
            return
        
        self.heartbeat_active = True
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_worker,
            daemon=True
        )
        self.heartbeat_thread.start()
        logger.info("WebSocket heartbeat monitoring started")
    
    def stop_heartbeat_monitoring(self) -> None:
        """Stop heartbeat monitoring."""
        self.heartbeat_active = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
        logger.info("WebSocket heartbeat monitoring stopped")
    
    def _register_handlers(self) -> None:
        """Register WebSocket event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect(auth=None):
            """Handle client connection."""
            try:
                connection_id = str(uuid.uuid4())
                
                # Get user and tenant context
                user_id = current_user.id if current_user and current_user.is_authenticated else None
                tenant_id = getattr(g, 'current_tenant', {}).get('id', None) if hasattr(g, 'current_tenant') else None
                
                # Create connection record
                connection = WebSocketConnection(
                    id=connection_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    ip_address=getattr(request, 'remote_addr', None) if 'request' in globals() else None,
                    metadata={'auth': auth} if auth else {}
                )
                
                self.connections[connection_id] = connection
                
                # Auto-join default rooms
                self._auto_join_rooms(connection_id, connection)
                
                # Update stats
                with self.stats_lock:
                    self.stats['connections_total'] += 1
                    self.stats['connections_active'] = len(self.connections)
                
                # Send welcome message
                self.emit_to_connection(connection_id, MessageType.SYSTEM_STATUS, {
                    'status': 'connected',
                    'connection_id': connection_id,
                    'server_time': datetime.now().isoformat(),
                    'rooms': list(connection.rooms)
                })
                
                logger.info(f"WebSocket client connected: {connection_id} (user: {user_id}, tenant: {tenant_id})")
                
            except Exception as e:
                logger.error(f"Error handling WebSocket connection: {e}")
                disconnect()
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            try:
                # Find connection by session
                connection_id = None
                for cid, conn in self.connections.items():
                    if conn.user_id == (current_user.id if current_user and current_user.is_authenticated else None):
                        connection_id = cid
                        break
                
                if connection_id:
                    self._cleanup_connection(connection_id)
                
                logger.info(f"WebSocket client disconnected: {connection_id}")
                
            except Exception as e:
                logger.error(f"Error handling WebSocket disconnection: {e}")
        
        @self.socketio.on('heartbeat')
        def handle_heartbeat(data=None):
            """Handle client heartbeat."""
            try:
                connection_id = self._get_connection_id_from_session()
                if connection_id and connection_id in self.connections:
                    self.connections[connection_id].last_heartbeat = datetime.now()
                    
                    # Send heartbeat response
                    emit('heartbeat_ack', {
                        'server_time': datetime.now().isoformat(),
                        'connection_id': connection_id
                    })
                
            except Exception as e:
                logger.error(f"Error handling heartbeat: {e}")
        
        @self.socketio.on('join_room')
        def handle_join_room(data):
            """Handle room join request."""
            try:
                room = data.get('room')
                if not room:
                    return
                
                connection_id = self._get_connection_id_from_session()
                if not connection_id or connection_id not in self.connections:
                    return
                
                connection = self.connections[connection_id]
                
                # Validate room access
                if self._can_join_room(connection, room):
                    self._join_room(connection_id, room)
                    emit('room_joined', {'room': room, 'status': 'success'})
                else:
                    emit('room_join_error', {'room': room, 'error': 'Access denied'})
                
            except Exception as e:
                logger.error(f"Error handling room join: {e}")
                emit('room_join_error', {'error': str(e)})
        
        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            """Handle room leave request."""
            try:
                room = data.get('room')
                if not room:
                    return
                
                connection_id = self._get_connection_id_from_session()
                if not connection_id or connection_id not in self.connections:
                    return
                
                self._leave_room(connection_id, room)
                emit('room_left', {'room': room, 'status': 'success'})
                
            except Exception as e:
                logger.error(f"Error handling room leave: {e}")
                emit('room_leave_error', {'error': str(e)})
        
        @self.socketio.on('subscribe')
        def handle_subscribe(data):
            """Handle event subscription."""
            try:
                event_types = data.get('events', [])
                connection_id = self._get_connection_id_from_session()
                
                if connection_id and connection_id in self.connections:
                    connection = self.connections[connection_id]
                    if 'subscriptions' not in connection.metadata:
                        connection.metadata['subscriptions'] = set()
                    
                    connection.metadata['subscriptions'].update(event_types)
                    emit('subscription_confirmed', {'events': event_types})
                
            except Exception as e:
                logger.error(f"Error handling subscription: {e}")
    
    def broadcast_message(self, message: WebSocketMessage) -> int:
        """Broadcast message to appropriate recipients."""
        try:
            recipients = 0
            
            if message.room:
                # Send to specific room
                self.socketio.emit(message.type.value, message.data, room=message.room)
                recipients = len(self.rooms.get(message.room, set()))
                
            elif message.target_user:
                # Send to specific user
                recipients = self._emit_to_user(message.target_user, message)
                
            elif message.target_tenant:
                # Send to specific tenant
                recipients = self._emit_to_tenant(message.target_tenant, message)
                
            else:
                # Broadcast to all connections
                self.socketio.emit(message.type.value, message.data)
                recipients = len(self.connections)
            
            # Update stats
            with self.stats_lock:
                self.message_stats['sent'] += recipients
            
            logger.debug(f"Broadcast message {message.type.value} to {recipients} recipients")
            return recipients
            
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
            with self.stats_lock:
                self.message_stats['errors'] += 1
            return 0
    
    def emit_to_connection(self, connection_id: str, message_type: MessageType, data: Dict[str, Any]) -> bool:
        """Emit message to specific connection."""
        try:
            message = WebSocketMessage(type=message_type, data=data)
            self.socketio.emit(message_type.value, data, room=connection_id)
            return True
            
        except Exception as e:
            logger.error(f"Error emitting to connection {connection_id}: {e}")
            return False
    
    def queue_message(self, message: WebSocketMessage) -> None:
        """Queue message for batch processing."""
        with self.queue_lock:
            self.message_queue.append(message)
    
    def process_message_queue(self) -> int:
        """Process queued messages."""
        with self.queue_lock:
            messages_to_process = self.message_queue[:]
            self.message_queue.clear()
        
        processed = 0
        for message in messages_to_process:
            if self.broadcast_message(message) > 0:
                processed += 1
        
        return processed
    
    def send_performance_update(self, metrics: Dict[str, Any]) -> None:
        """Send performance metrics update."""
        message = WebSocketMessage(
            type=MessageType.PERFORMANCE_UPDATE,
            data={
                'metrics': metrics,
                'timestamp': datetime.now().isoformat()
            },
            room='performance'
        )
        self.broadcast_message(message)
    
    def send_cache_stats_update(self, stats: Dict[str, Any]) -> None:
        """Send cache statistics update."""
        message = WebSocketMessage(
            type=MessageType.CACHE_STATS,
            data={
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            },
            room='performance'
        )
        self.broadcast_message(message)
    
    def send_analytics_update(self, analytics: Dict[str, Any]) -> None:
        """Send analytics update."""
        message = WebSocketMessage(
            type=MessageType.ANALYTICS_UPDATE,
            data={
                'analytics': analytics,
                'timestamp': datetime.now().isoformat()
            },
            room='analytics'
        )
        self.broadcast_message(message)
    
    def send_visualization_update(self, chart_type: str, chart_data: Dict[str, Any]) -> None:
        """Send visualization update to all clients."""
        message = WebSocketMessage(
            type=MessageType.ANALYTICS_UPDATE,  # Reuse existing message type for visualizations
            data={
                'visualization_update': True,
                'chart_type': chart_type,
                'chart_data': chart_data,
                'timestamp': datetime.now().isoformat()
            },
            room='analytics',
            priority="normal"
        )
        self.broadcast_message(message)
    
    def send_alert_notification(self, alert: Dict[str, Any], priority: str = "normal") -> None:
        """Send alert notification."""
        message = WebSocketMessage(
            type=MessageType.ALERT_NOTIFICATION,
            data={
                'alert': alert,
                'timestamp': datetime.now().isoformat()
            },
            room='alerts',
            priority=priority
        )
        self.broadcast_message(message)
    
    def send_tenant_update(self, tenant_id: str, update: Dict[str, Any]) -> None:
        """Send tenant-specific update."""
        message = WebSocketMessage(
            type=MessageType.TENANT_UPDATE,
            data={
                'update': update,
                'timestamp': datetime.now().isoformat()
            },
            target_tenant=tenant_id
        )
        self.broadcast_message(message)
    
    def trigger_dashboard_refresh(self, components: List[str] = None) -> None:
        """Trigger dashboard refresh for all clients."""
        message = WebSocketMessage(
            type=MessageType.DASHBOARD_REFRESH,
            data={
                'components': components or ['all'],
                'timestamp': datetime.now().isoformat()
            }
        )
        self.broadcast_message(message)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        with self.stats_lock:
            active_connections = len(self.connections)
            
            # Group by tenant and user
            tenant_connections = {}
            user_connections = {}
            
            for conn in self.connections.values():
                if conn.tenant_id:
                    tenant_connections[conn.tenant_id] = tenant_connections.get(conn.tenant_id, 0) + 1
                if conn.user_id:
                    user_connections[conn.user_id] = user_connections.get(conn.user_id, 0) + 1
            
            return {
                'active_connections': active_connections,
                'total_connections': self.message_stats['connections_total'],
                'messages_sent': self.message_stats['sent'],
                'messages_received': self.message_stats['received'],
                'message_errors': self.message_stats['errors'],
                'tenant_connections': tenant_connections,
                'user_connections': user_connections,
                'active_rooms': len(self.rooms),
                'queued_messages': len(self.message_queue)
            }
    
    def get_room_info(self, room: str) -> Dict[str, Any]:
        """Get information about a specific room."""
        if room not in self.rooms:
            return {'exists': False}
        
        connection_ids = self.rooms[room]
        connections = [self.connections[cid] for cid in connection_ids if cid in self.connections]
        
        return {
            'exists': True,
            'member_count': len(connections),
            'members': [{
                'connection_id': conn.id,
                'user_id': conn.user_id,
                'tenant_id': conn.tenant_id,
                'connected_at': conn.connected_at.isoformat(),
                'last_heartbeat': conn.last_heartbeat.isoformat()
            } for conn in connections]
        }
    
    def _auto_join_rooms(self, connection_id: str, connection: WebSocketConnection) -> None:
        """Auto-join default rooms based on user context."""
        # Global room for all users
        self._join_room(connection_id, 'global')
        
        # User-specific room
        if connection.user_id:
            self._join_room(connection_id, f"user:{connection.user_id}")
        
        # Tenant-specific room
        if connection.tenant_id:
            self._join_room(connection_id, f"tenant:{connection.tenant_id}")
        
        # Admin room for admin users
        if connection.user_id and self._is_admin_user(connection.user_id):
            self._join_room(connection_id, 'admin')
    
    def _join_room(self, connection_id: str, room: str) -> None:
        """Join connection to room."""
        if connection_id in self.connections:
            join_room(room)
            self.connections[connection_id].rooms.add(room)
            
            if room not in self.rooms:
                self.rooms[room] = set()
            self.rooms[room].add(connection_id)
    
    def _leave_room(self, connection_id: str, room: str) -> None:
        """Leave connection from room."""
        if connection_id in self.connections:
            leave_room(room)
            self.connections[connection_id].rooms.discard(room)
            
            if room in self.rooms:
                self.rooms[room].discard(connection_id)
                if not self.rooms[room]:
                    del self.rooms[room]
    
    def _cleanup_connection(self, connection_id: str) -> None:
        """Clean up connection and remove from rooms."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        # Remove from all rooms
        for room in connection.rooms.copy():
            self._leave_room(connection_id, room)
        
        # Remove connection
        del self.connections[connection_id]
        
        # Update stats
        with self.stats_lock:
            self.message_stats['connections_active'] = len(self.connections)
    
    def _can_join_room(self, connection: WebSocketConnection, room: str) -> bool:
        """Check if connection can join room."""
        # Public rooms
        if room in ['global', 'performance', 'analytics']:
            return True
        
        # User-specific rooms
        if room.startswith('user:'):
            user_id = room[5:]  # Remove 'user:' prefix
            return connection.user_id == user_id
        
        # Tenant-specific rooms
        if room.startswith('tenant:'):
            tenant_id = room[7:]  # Remove 'tenant:' prefix
            return connection.tenant_id == tenant_id
        
        # Admin rooms
        if room == 'admin':
            return self._is_admin_user(connection.user_id)
        
        # Alert rooms require authentication
        if room == 'alerts':
            return connection.user_id is not None
        
        return False
    
    def _is_admin_user(self, user_id: str) -> bool:
        """Check if user is admin."""
        # This would check the user's role in the database
        # For now, return False as a placeholder
        return False
    
    def _get_connection_id_from_session(self) -> Optional[str]:
        """Get connection ID from current session."""
        # This would extract connection ID from Flask-SocketIO session
        # For now, return None as a placeholder
        return None
    
    def _emit_to_user(self, user_id: str, message: WebSocketMessage) -> int:
        """Emit message to all connections for a specific user."""
        count = 0
        user_connections = [conn for conn in self.connections.values() if conn.user_id == user_id]
        
        for connection in user_connections:
            if self.emit_to_connection(connection.id, message.type, message.data):
                count += 1
        
        return count
    
    def _emit_to_tenant(self, tenant_id: str, message: WebSocketMessage) -> int:
        """Emit message to all connections for a specific tenant."""
        count = 0
        tenant_connections = [conn for conn in self.connections.values() if conn.tenant_id == tenant_id]
        
        for connection in tenant_connections:
            if self.emit_to_connection(connection.id, message.type, message.data):
                count += 1
        
        return count
    
    def _heartbeat_worker(self) -> None:
        """Background worker for heartbeat monitoring."""
        while self.heartbeat_active:
            try:
                current_time = datetime.now()
                stale_connections = []
                
                for connection_id, connection in self.connections.items():
                    if (current_time - connection.last_heartbeat).total_seconds() > self.heartbeat_timeout:
                        stale_connections.append(connection_id)
                
                # Clean up stale connections
                for connection_id in stale_connections:
                    logger.warning(f"Removing stale WebSocket connection: {connection_id}")
                    self._cleanup_connection(connection_id)
                
                # Send heartbeat to active connections
                heartbeat_message = WebSocketMessage(
                    type=MessageType.HEARTBEAT,
                    data={'server_time': current_time.isoformat()}
                )
                self.broadcast_message(heartbeat_message)
                
                time.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Error in heartbeat worker: {e}")
                time.sleep(self.heartbeat_interval)


# Global WebSocket service instance will be initialized with Flask-SocketIO
websocket_service: Optional[WebSocketService] = None


def init_websocket_service(socketio: SocketIO) -> WebSocketService:
    """Initialize the global WebSocket service."""
    global websocket_service
    websocket_service = WebSocketService(socketio)
    websocket_service.start_heartbeat_monitoring()
    return websocket_service


def get_websocket_service() -> Optional[WebSocketService]:
    """Get the global WebSocket service instance."""
    return websocket_service