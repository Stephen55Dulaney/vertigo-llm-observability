# EOD Prompt A/B Testing Setup

## 🎯 Overview

This setup provides everything you need to test and improve the End-of-Day (EOD) prompt using A/B testing. The current EOD prompt is broken, and we need to create a Version 2 using the A/B testing framework.

## 📊 Data Store Information

**EOD Prompt Data Source:** Firestore `meetings` collection

**Data Structure:**
- **Collection:** `meetings`
- **Query Pattern:** Recent meetings (last 24 hours) for specific project
- **Key Fields:**
  - `transcript`: Raw meeting transcript
  - `processed_notes`: AI-generated summary
  - `structured_data`: Extracted metadata (participants, action items, blockers)
  - `gemini_result`: Full AI analysis
  - `semantic_tags`: Categorized topics and sentiment
  - `metadata`: Meeting details (title, duration, participants)
  - `project`: Project identifier
  - `timestamp`: Meeting date/time

## 🧪 Test Data Created

**File:** `test_eod_firestore_data.json`

**Contents:**
- 5 realistic meeting records (August 2, 2025 - last 24 hours)
- Covers standups, client demos, technical reviews, progress checks, and client feedback
- Includes all required fields that the EOD prompt would use
- Represents typical Vertigo project data with varied meeting types

**Meeting Types:**
1. **Morning Standup** - Daily coordination and blocker resolution
2. **Client Demo** - Product presentation and technical showcase
3. **Technical Deep Dive** - Architecture and implementation details
4. **Progress Check** - Status updates and timeline review
5. **Client Feedback** - Post-demo feedback and next phase planning

## 🎨 EOD Prompt Variants Created

### Variant A: Executive Focus
- **Approach:** Executive-level summary with high-level insights
- **Structure:** Key accomplishments, critical decisions, blockers, next week focus, metrics
- **Tone:** Professional but conversational
- **Target:** Executive stakeholders

### Variant B: Technical Deep Dive
- **Approach:** Comprehensive technical analysis
- **Structure:** Technical progress, development status, challenges, priorities, team capacity
- **Tone:** Technical and detailed
- **Target:** Technical team and architects

### Variant C: Action-Oriented
- **Approach:** Task-focused with clear next steps
- **Structure:** Accomplishments, action items, blockers, success metrics, team coordination
- **Tone:** Actionable and specific
- **Target:** Project managers and team leads

## 🚀 How to Use

### 1. Test the Setup
```bash
cd vertigo-debug-toolkit
python test_eod_ab_testing.py
```

### 2. Generated Files
- `test_eod_firestore_data.json` - Test data simulating Firestore
- `eod_prompt_variants_YYYYMMDD_HHMMSS.json` - Generated prompt variants
- `test_eod_ab_testing.py` - Testing script

### 3. A/B Testing Process
1. **Load test data** into the A/B testing framework
2. **Run each variant** against the test data
3. **Evaluate results** using the framework's criteria:
   - Accuracy (40% weight)
   - Completeness (30% weight)
   - Clarity (20% weight)
   - Cost efficiency (10% weight)
4. **Compare performance** and select the best variant
5. **Deploy the winner** as EOD Prompt Version 2

## 📈 Evaluation Criteria

The A/B testing framework evaluates prompts on:

- **Accuracy (40%):** How accurately does output match expected result?
- **Completeness (30%):** How complete is the output?
- **Clarity (20%):** How clear and well-structured is the output?
- **Cost Efficiency (10%):** How cost-effective is the prompt?

## 🔧 Integration Points

**Current EOD Prompt Flow:**
1. Email processor receives EOD trigger
2. Queries Firestore for recent meetings (24 hours)
3. Processes meeting data through EOD prompt
4. Generates summary and sends via email

**A/B Testing Integration:**
1. Use test data to validate prompt variants
2. Compare performance metrics
3. Select best performing variant
4. Deploy to production

## 📋 Next Steps

1. **Run A/B Tests:** Use the framework to test all three variants
2. **Evaluate Results:** Compare performance metrics
3. **Select Winner:** Choose the best performing variant
4. **Deploy Version 2:** Replace the broken EOD prompt
5. **Monitor Performance:** Track real-world performance

## 🎯 Success Metrics

- **Accuracy:** EOD summaries should capture key insights accurately
- **Completeness:** Should include all critical information from meetings
- **Clarity:** Executives should understand the summary immediately
- **Actionability:** Should drive clear next steps and decisions

## 📁 Files Created

- `test_eod_firestore_data.json` - Test data
- `test_eod_ab_testing.py` - Testing script
- `eod_prompt_variants_*.json` - Generated variants
- `EOD_AB_TESTING_SETUP.md` - This documentation

Ready for A/B testing! 🚀 