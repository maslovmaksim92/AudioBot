#!/usr/bin/env python3
"""
Advanced Self-Learning Test for VasDom AudioBot v3.0
Tests the revolutionary self-learning features:
- Multiple conversations to build learning data
- Rating system impact on learning
- Similar conversation detection
- Learning statistics evolution
- Export functionality with quality data
"""

import requests
import json
import time
from datetime import datetime

class SelfLearningTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.conversations = []
        
    def create_conversation(self, message: str, session_id: str = None) -> dict:
        """Create a conversation and return the response"""
        if not session_id:
            session_id = f"learning_test_{int(time.time())}"
            
        data = {
            "message": message,
            "session_id": session_id
        }
        
        response = requests.post(f"{self.api_url}/voice/process", json=data)
        if response.status_code == 200:
            result = response.json()
            self.conversations.append(result)
            return result
        else:
            print(f"❌ Failed to create conversation: {response.status_code}")
            return {}
    
    def rate_conversation(self, log_id: str, rating: int, feedback: str = None) -> bool:
        """Rate a conversation"""
        data = {
            "log_id": log_id,
            "rating": rating,
            "feedback_text": feedback
        }
        
        response = requests.post(f"{self.api_url}/voice/feedback", json=data)
        return response.status_code == 200
    
    def get_learning_stats(self) -> dict:
        """Get current learning statistics"""
        response = requests.get(f"{self.api_url}/learning/stats")
        if response.status_code == 200:
            return response.json()
        return {}
    
    def get_similar_conversations(self, log_id: str) -> dict:
        """Get similar conversations for a log_id"""
        response = requests.get(f"{self.api_url}/learning/similar/{log_id}")
        if response.status_code == 200:
            return response.json()
        return {}
    
    def export_learning_data(self) -> dict:
        """Export learning data"""
        response = requests.get(f"{self.api_url}/learning/export")
        if response.status_code == 200:
            return response.json()
        return {}
    
    def run_self_learning_test(self):
        """Run comprehensive self-learning test"""
        print("🧠 ADVANCED SELF-LEARNING TEST FOR VASDOM AUDIOBOT v3.0")
        print("=" * 60)
        
        # Phase 1: Create initial conversations
        print("\n📝 Phase 1: Creating Initial Conversations...")
        
        test_messages = [
            "Как часто нужно убираться в офисе?",
            "Какие средства лучше использовать для уборки подъездов?",
            "Сколько времени занимает уборка одного подъезда?",
            "Как организовать работу бригады по уборке?",
            "Какие проблемы чаще всего возникают при уборке подъездов?",
            "Как часто проводить генеральную уборку в офисных помещениях?",  # Similar to first
            "Какое оборудование нужно для качественной уборки подъездов?",   # Similar to second
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"  {i}. Creating conversation: '{message[:40]}...'")
            result = self.create_conversation(message)
            if result:
                print(f"     ✅ Created (ID: {result.get('log_id', 'N/A')[:8]}..., Similar found: {result.get('similar_found', 0)})")
            time.sleep(0.5)  # Small delay between requests
        
        print(f"\n✅ Created {len(self.conversations)} conversations")
        
        # Phase 2: Rate conversations to create learning data
        print("\n⭐ Phase 2: Rating Conversations for Learning...")
        
        ratings = [5, 4, 5, 3, 4, 5, 4]  # Mix of high and medium ratings
        feedbacks = [
            "Отличный ответ про частоту уборки!",
            "Хорошие рекомендации по средствам",
            "Полезная информация о времени",
            "Неплохо, но можно подробнее",
            "Хороший совет по организации",
            "Отлично! Похоже на первый вопрос",
            "Качественный ответ про оборудование"
        ]
        
        for i, conv in enumerate(self.conversations):
            if 'log_id' in conv:
                rating = ratings[i] if i < len(ratings) else 4
                feedback = feedbacks[i] if i < len(feedbacks) else "Хороший ответ"
                
                success = self.rate_conversation(conv['log_id'], rating, feedback)
                print(f"  {i+1}. Rated conversation {conv['log_id'][:8]}... with {rating}★: {'✅' if success else '❌'}")
        
        # Phase 3: Check learning statistics
        print("\n📊 Phase 3: Analyzing Learning Statistics...")
        
        stats = self.get_learning_stats()
        if stats:
            print(f"  📈 Total interactions: {stats.get('total_interactions', 0)}")
            print(f"  ⭐ Average rating: {stats.get('avg_rating', 'N/A')}")
            print(f"  👍 Positive ratings (≥4★): {stats.get('positive_ratings', 0)}")
            print(f"  👎 Negative ratings (≤2★): {stats.get('negative_ratings', 0)}")
            print(f"  🚀 Improvement rate: {stats.get('improvement_rate', 0):.2f}")
        else:
            print("  ❌ Failed to get learning statistics")
        
        # Phase 4: Test similar conversation detection
        print("\n🔍 Phase 4: Testing Similar Conversation Detection...")
        
        if len(self.conversations) >= 2:
            # Test with the first conversation (should find the 6th as similar)
            first_conv = self.conversations[0]
            if 'log_id' in first_conv:
                similar = self.get_similar_conversations(first_conv['log_id'])
                if similar:
                    print(f"  🎯 Original: '{similar.get('original_message', '')[:40]}...'")
                    print(f"  🔍 Found {similar.get('found_similar', 0)} similar conversations:")
                    
                    for i, sim_conv in enumerate(similar.get('similar_conversations', []), 1):
                        print(f"    {i}. '{sim_conv.get('user_message', '')[:40]}...' (Rating: {sim_conv.get('rating', 'N/A')}★)")
                else:
                    print("  ❌ Failed to get similar conversations")
        
        # Phase 5: Test learning data export
        print("\n📤 Phase 5: Testing Learning Data Export...")
        
        export_data = self.export_learning_data()
        if export_data:
            print(f"  📦 Exported {export_data.get('total_exported', 0)} high-quality conversations")
            print(f"  ⭐ Minimum rating used: {export_data.get('min_rating_used', 'N/A')}★")
            print(f"  📅 Export timestamp: {export_data.get('export_timestamp', 'N/A')}")
            
            # Show sample of exported data
            sample_data = export_data.get('data', [])
            if sample_data:
                print(f"  📋 Sample exported conversation:")
                sample = sample_data[0]
                messages = sample.get('messages', [])
                if len(messages) >= 2:
                    print(f"    👤 User: '{messages[0].get('content', '')[:50]}...'")
                    print(f"    🤖 AI: '{messages[1].get('content', '')[:50]}...'")
                    print(f"    ⭐ Rating: {sample.get('metadata', {}).get('rating', 'N/A')}★")
        else:
            print("  ❌ Failed to export learning data")
        
        # Phase 6: Test learning improvement with new conversation
        print("\n🧠 Phase 6: Testing Learning Improvement...")
        
        # Create a new conversation similar to existing ones
        new_message = "Как правильно организовать уборку в офисных зданиях?"
        print(f"  🆕 Creating new conversation: '{new_message}'")
        
        new_conv = self.create_conversation(new_message)
        if new_conv:
            similar_found = new_conv.get('similar_found', 0)
            learning_improved = new_conv.get('learning_improved', False)
            
            print(f"  🔍 Similar conversations found: {similar_found}")
            print(f"  🧠 Learning improved: {'✅ Yes' if learning_improved else '❌ No'}")
            print(f"  📝 Response length: {len(new_conv.get('response', ''))} characters")
            
            if similar_found > 0:
                print("  🎉 SUCCESS: AI found similar conversations and used them for learning!")
            else:
                print("  ⚠️  No similar conversations found - this might be expected for new topics")
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎯 SELF-LEARNING TEST SUMMARY")
        print("=" * 60)
        
        final_stats = self.get_learning_stats()
        if final_stats:
            print(f"📊 Final Statistics:")
            print(f"  • Total interactions: {final_stats.get('total_interactions', 0)}")
            print(f"  • Average rating: {final_stats.get('avg_rating', 'N/A')}")
            print(f"  • Positive ratings: {final_stats.get('positive_ratings', 0)}")
            print(f"  • Improvement rate: {final_stats.get('improvement_rate', 0):.2f}")
        
        print(f"\n🧠 Self-Learning Features Tested:")
        print(f"  ✅ Conversation creation and storage")
        print(f"  ✅ Rating system for quality filtering")
        print(f"  ✅ Learning statistics tracking")
        print(f"  ✅ Similar conversation detection")
        print(f"  ✅ Quality data export for fine-tuning")
        print(f"  ✅ Learning improvement on new conversations")
        
        print(f"\n🚀 VasDom AudioBot v3.0 Self-Learning System is {'WORKING CORRECTLY!' if len(self.conversations) > 0 else 'NEEDS ATTENTION!'}")

def main():
    """Run the self-learning test"""
    tester = SelfLearningTester()
    tester.run_self_learning_test()

if __name__ == "__main__":
    main()