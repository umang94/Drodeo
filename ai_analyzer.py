"""
AI Analyzer for Video Processing
Integrates OpenAI GPT-4 Vision for intelligent keyframe analysis and clip enhancement.
"""

import base64
import cv2
import numpy as np
from typing import List, Dict, Optional
import os
from openai import OpenAI
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class AIAnalyzer:
    """Handles OpenAI GPT-4 Vision integration for video analysis."""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("   ⚠️  No OpenAI API key found - AI analysis will be skipped")
            self.client = None
            self.model = "gpt-4o"
            self.max_tokens = 300
            self.temperature = 0.3
            return
        
        # Initialize OpenAI client with proper parameters for version 1.101.0
        try:
            self.client = OpenAI(api_key=api_key)
            print(f"   ✅ OpenAI client initialized successfully (version 1.101.0)")
        except Exception as e:
            print(f"   ❌ OpenAI client initialization failed: {e}")
            self.client = None
        
        self.model = "gpt-4o"
        self.max_tokens = 300
        self.temperature = 0.3
    
    def _encode_frame_to_base64(self, frame: np.ndarray) -> str:
        """Convert OpenCV frame to base64 string for API."""
        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        # Convert to base64
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        return frame_base64
    
    def analyze_single_frame(self, frame: np.ndarray, context: str = "") -> Dict:
        """Analyze a single frame with GPT-4 Vision."""
        try:
            frame_base64 = self._encode_frame_to_base64(frame)
            
            # Create the prompt for drone video analysis
            prompt = f"""Analyze this drone video frame and provide a JSON response with the following information:

1. scene_type: What type of scene is this? (landscape, cityscape, water, forest, mountains, buildings, etc.)
2. visual_quality: Rate the visual quality from 1-10 (consider lighting, clarity, composition)
3. interest_level: Rate how visually interesting/engaging this scene is from 1-10
4. lighting_condition: Describe the lighting (golden_hour, overcast, bright_daylight, sunset, etc.)
5. motion_indicators: Any visible signs of camera movement or subject motion
6. scenic_beauty: Rate the scenic beauty from 1-10
7. composition_quality: Rate the composition and framing from 1-10
8. description: Brief description of what's visible in the frame
9. theme_suitability: Which themes would this scene work best for? (happy, exciting, peaceful, adventure, cinematic)

{context}

Respond only with valid JSON format."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{frame_base64}",
                                    "detail": "low"  # Use low detail for cost efficiency
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content
            try:
                analysis = json.loads(content)
                analysis['api_cost'] = self._estimate_cost(response)
                return analysis
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    'scene_type': 'unknown',
                    'visual_quality': 5,
                    'interest_level': 5,
                    'lighting_condition': 'unknown',
                    'motion_indicators': 'unknown',
                    'scenic_beauty': 5,
                    'composition_quality': 5,
                    'description': content[:100] if content else 'Analysis failed',
                    'theme_suitability': ['cinematic'],
                    'api_cost': self._estimate_cost(response),
                    'parse_error': True
                }
                
        except Exception as e:
            print(f"   ⚠️  AI analysis failed: {e}")
            return {
                'scene_type': 'error',
                'visual_quality': 5,
                'interest_level': 5,
                'lighting_condition': 'unknown',
                'motion_indicators': 'unknown',
                'scenic_beauty': 5,
                'composition_quality': 5,
                'description': f'Error: {str(e)}',
                'theme_suitability': ['cinematic'],
                'api_cost': 0.0,
                'error': True
            }
    
    def analyze_keyframes_batch(self, keyframes: List[np.ndarray], video_name: str = "") -> List[Dict]:
        """Analyze multiple keyframes from a video."""
        print(f"   🤖 Analyzing {len(keyframes)} keyframes with AI...")
        
        analyses = []
        total_cost = 0.0
        
        for i, frame in enumerate(keyframes):
            print(f"      Frame {i+1}/{len(keyframes)}...", end=" ")
            
            context = f"This is keyframe {i+1} of {len(keyframes)} from drone video: {video_name}"
            analysis = self.analyze_single_frame(frame, context)
            analyses.append(analysis)
            
            if 'api_cost' in analysis:
                total_cost += analysis['api_cost']
            
            print("✓")
        
        print(f"   💰 Estimated API cost: ${total_cost:.3f}")
        return analyses
    
    def _estimate_cost(self, response) -> float:
        """Estimate the cost of the API call."""
        # GPT-4 Vision pricing (approximate)
        # Input: $0.01 per 1K tokens, Output: $0.03 per 1K tokens
        # Images: $0.00765 per image (low detail)
        
        try:
            input_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') else 1000
            output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') else 100
            
            input_cost = (input_tokens / 1000) * 0.01
            output_cost = (output_tokens / 1000) * 0.03
            image_cost = 0.00765  # Per image
            
            return input_cost + output_cost + image_cost
        except:
            return 0.01  # Default estimate
    
    def enhance_clip_scoring(self, clips: List, ai_analyses: List[Dict]) -> List:
        """Enhance clip scoring using AI analysis results."""
        if not ai_analyses or len(ai_analyses) == 0:
            return clips
        
        print(f"   🎯 Enhancing {len(clips)} clips with AI insights...")
        
        # Calculate average AI scores for the video
        avg_visual_quality = np.mean([a.get('visual_quality', 5) for a in ai_analyses])
        avg_interest_level = np.mean([a.get('interest_level', 5) for a in ai_analyses])
        avg_scenic_beauty = np.mean([a.get('scenic_beauty', 5) for a in ai_analyses])
        avg_composition = np.mean([a.get('composition_quality', 5) for a in ai_analyses])
        
        # Enhance each clip's scoring
        enhanced_clips = []
        for clip in clips:
            # Create enhanced clip with AI-based adjustments
            ai_quality_bonus = (avg_visual_quality / 10.0) * 0.2  # Up to 20% bonus
            ai_interest_bonus = (avg_interest_level / 10.0) * 0.15  # Up to 15% bonus
            ai_beauty_bonus = (avg_scenic_beauty / 10.0) * 0.15   # Up to 15% bonus
            ai_composition_bonus = (avg_composition / 10.0) * 0.1  # Up to 10% bonus
            
            # Apply AI enhancements to quality score
            original_score = clip.quality_score
            enhanced_score = original_score * (1 + ai_quality_bonus + ai_interest_bonus + 
                                             ai_beauty_bonus + ai_composition_bonus)
            
            # Cap the score at 1.0
            enhanced_score = min(enhanced_score, 1.0)
            
            # Update clip with enhanced scoring
            clip.quality_score = enhanced_score
            
            # Add AI description if available
            if ai_analyses:
                # Use the most relevant AI analysis (middle keyframe)
                mid_analysis = ai_analyses[len(ai_analyses)//2]
                clip.description = f"{clip.description} | AI: {mid_analysis.get('description', 'N/A')}"
            
            enhanced_clips.append(clip)
        
        # Re-sort clips by enhanced quality score
        enhanced_clips.sort(key=lambda x: x.quality_score, reverse=True)
        
        print(f"   ✨ Enhanced scoring complete (avg boost: {((avg_visual_quality + avg_interest_level + avg_scenic_beauty + avg_composition) / 40.0) * 100:.1f}%)")
        
        return enhanced_clips
    
    def get_theme_recommendations(self, ai_analyses: List[Dict]) -> Dict[str, float]:
        """Get theme recommendations based on AI analysis."""
        if not ai_analyses:
            return {}
        
        theme_scores = {
            'happy': 0.0,
            'exciting': 0.0,
            'peaceful': 0.0,
            'adventure': 0.0,
            'cinematic': 0.0
        }
        
        for analysis in ai_analyses:
            # Extract theme suitability
            suitable_themes = analysis.get('theme_suitability', [])
            if isinstance(suitable_themes, list):
                for theme in suitable_themes:
                    if theme.lower() in theme_scores:
                        theme_scores[theme.lower()] += 1.0
            
            # Boost scores based on other factors
            visual_quality = analysis.get('visual_quality', 5) / 10.0
            interest_level = analysis.get('interest_level', 5) / 10.0
            scenic_beauty = analysis.get('scenic_beauty', 5) / 10.0
            
            # Scene type influences
            scene_type = analysis.get('scene_type', '').lower()
            if 'water' in scene_type or 'ocean' in scene_type:
                theme_scores['peaceful'] += 0.5
                theme_scores['cinematic'] += 0.3
            elif 'mountain' in scene_type or 'landscape' in scene_type:
                theme_scores['adventure'] += 0.5
                theme_scores['cinematic'] += 0.4
            elif 'city' in scene_type or 'urban' in scene_type:
                theme_scores['exciting'] += 0.4
                theme_scores['cinematic'] += 0.3
            
            # Lighting influences
            lighting = analysis.get('lighting_condition', '').lower()
            if 'golden' in lighting or 'sunset' in lighting:
                theme_scores['cinematic'] += 0.6
                theme_scores['peaceful'] += 0.3
            elif 'bright' in lighting:
                theme_scores['happy'] += 0.4
                theme_scores['exciting'] += 0.2
        
        # Normalize scores
        max_score = max(theme_scores.values()) if theme_scores.values() else 1.0
        if max_score > 0:
            theme_scores = {k: v/max_score for k, v in theme_scores.items()}
        
        return theme_scores

def analyze_video_with_ai(keyframes: List[np.ndarray], video_name: str = "") -> Optional[List[Dict]]:
    """Convenience function to analyze video keyframes with AI."""
    try:
        analyzer = AIAnalyzer()
        if analyzer.client is None:
            print(f"   ⚠️  Skipping AI analysis - no OpenAI client available")
            return None
        
        print(f"   🚀 Starting OpenAI API calls for {video_name}...")
        result = analyzer.analyze_keyframes_batch(keyframes, video_name)
        
        if result:
            print(f"   ✅ AI analysis completed successfully - {len(result)} frames analyzed")
        else:
            print(f"   ⚠️  AI analysis returned no results")
            
        return result
    except Exception as e:
        print(f"   ❌ AI analysis failed: {e}")
        return None
