#!/usr/bin/env python3
"""
语音识别和分析专项示例

展示语音识别服务的各种功能，包括：
- 单个音频文件处理
- 批量音频处理
- 音频质量验证
- 多语言支持

运行方式:
    python examples/speech_analysis_example.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.speech_recognition_service import SpeechRecognitionService

class SpeechAnalysisExample:
    """语音分析示例类"""
    
    def __init__(self):
        self.speech_service = SpeechRecognitionService()
    
    async def single_audio_analysis(self):
        """单个音频分析示例"""
        print("🎤 单个音频分析示例")
        print("-" * 30)
        
        # 模拟音频数据
        audio_data = b"customer_inquiry_audio_sample" * 100
        
        try:
            # 执行语音识别
            result = await self.speech_service.transcribe_audio(
                audio_data, 
                format='wav',
                language='zh-CN'
            )
            
            # 显示详细结果
            print(f"📝 转录文本: {result.transcript}")
            print(f"🎯 置信度: {result.confidence:.2%}")
            print(f"😊 情感分析: {result.sentiment}")
            print(f"🎭 情绪识别: {result.emotion}")
            print(f"🗣️  语速: {result.speaking_rate:.1f} 词/分钟")
            print(f"⏸️  停顿频率: {result.pause_frequency:.2f}")
            print(f"🔊 语音质量:")
            for quality_metric, score in result.voice_quality.items():
                print(f"     {quality_metric}: {score:.2f}")
            print(f"🔑 关键词: {', '.join(result.keywords)}")
            print(f"💡 意图识别: {result.intent or '未识别'}")
            
        except Exception as e:
            print(f"❌ 分析失败: {str(e)}")
    
    async def batch_audio_analysis(self):
        """批量音频分析示例"""
        print("\n🎵 批量音频分析示例")
        print("-" * 30)
        
        # 模拟多个音频文件
        audio_files = [
            {
                'data': b"product_inquiry_audio" * 80,
                'format': 'wav',
                'description': '产品咨询'
            },
            {
                'data': b"price_question_audio" * 120,
                'format': 'mp3',
                'description': '价格询问'
            },
            {
                'data': b"technical_support_audio" * 150,
                'format': 'flac',
                'description': '技术支持'
            }
        ]
        
        print(f"📁 准备处理 {len(audio_files)} 个音频文件")
        
        try:
            # 执行批量处理
            results = await self.speech_service.batch_transcribe(audio_files)
            
            print("✅ 批量处理完成")
            print("\n📊 处理结果汇总:")
            
            for i, (audio_file, result) in enumerate(zip(audio_files, results), 1):
                print(f"\n{i}. {audio_file['description']} ({audio_file['format']})")
                print(f"   转录: {result.transcript[:50]}...")
                print(f"   置信度: {result.confidence:.2%}")
                print(f"   情感: {result.sentiment}")
                print(f"   关键词: {', '.join(result.keywords[:3])}")
            
        except Exception as e:
            print(f"❌ 批量处理失败: {str(e)}")
    
    async def audio_quality_validation(self):
        """音频质量验证示例"""
        print("\n🔍 音频质量验证示例")
        print("-" * 30)
        
        # 测试不同质量的音频
        audio_samples = [
            {
                'name': '高质量音频',
                'data': b"high_quality_audio_sample" * 200,
                'expected': '高质量'
            },
            {
                'name': '中等质量音频',
                'data': b"medium_quality_audio" * 100,
                'expected': '中等质量'
            },
            {
                'name': '低质量音频',
                'data': b"low_quality" * 30,
                'expected': '低质量'
            }
        ]
        
        for sample in audio_samples:
            print(f"\n🎧 验证 {sample['name']}")
            
            try:
                quality_result = await self.speech_service.validate_audio_quality(
                    sample['data']
                )
                
                print(f"   质量评分: {quality_result['quality_score']:.2f}")
                print(f"   是否有效: {'✅' if quality_result['is_valid'] else '❌'}")
                
                if quality_result['issues']:
                    print(f"   发现问题: {', '.join(quality_result['issues'])}")
                
                if quality_result['recommendations']:
                    print("   改进建议:")
                    for rec in quality_result['recommendations']:
                        print(f"     • {rec}")
                
            except Exception as e:
                print(f"   ❌ 验证失败: {str(e)}")
    
    async def language_support_demo(self):
        """多语言支持演示"""
        print("\n🌍 多语言支持演示")
        print("-" * 30)
        
        try:
            # 获取支持的语言列表
            supported_languages = await self.speech_service.get_supported_languages()
            
            print("🗣️  支持的语言:")
            for lang in supported_languages:
                lang_names = {
                    'zh-CN': '中文(简体)',
                    'zh-TW': '中文(繁体)',
                    'en-US': '英语(美国)',
                    'en-GB': '英语(英国)',
                    'ja-JP': '日语',
                    'ko-KR': '韩语'
                }
                print(f"   • {lang}: {lang_names.get(lang, '未知语言')}")
            
            # 演示不同语言的处理
            print("\n🎯 多语言处理演示:")
            
            language_samples = [
                ('zh-CN', b"chinese_audio_sample" * 80),
                ('en-US', b"english_audio_sample" * 90),
                ('ja-JP', b"japanese_audio_sample" * 70)
            ]
            
            for lang_code, audio_data in language_samples:
                try:
                    result = await self.speech_service.transcribe_audio(
                        audio_data, 
                        format='wav',
                        language=lang_code
                    )
                    
                    lang_name = {
                        'zh-CN': '中文', 'en-US': '英语', 'ja-JP': '日语'
                    }.get(lang_code, lang_code)
                    
                    print(f"   {lang_name}: {result.transcript[:30]}... (置信度: {result.confidence:.2%})")
                    
                except Exception as e:
                    print(f"   {lang_code}: ❌ 处理失败 - {str(e)}")
            
        except Exception as e:
            print(f"❌ 语言支持演示失败: {str(e)}")
    
    async def error_handling_demo(self):
        """错误处理演示"""
        print("\n⚠️  错误处理演示")
        print("-" * 30)
        
        # 测试各种错误情况
        error_cases = [
            {
                'name': '不支持的音频格式',
                'data': b"test_audio" * 50,
                'format': 'xyz',
                'expected_error': '不支持的音频格式'
            },
            {
                'name': '音频文件过大',
                'data': b"x" * (51 * 1024 * 1024),  # 51MB
                'format': 'wav',
                'expected_error': '音频文件过大'
            }
        ]
        
        for case in error_cases:
            print(f"\n🧪 测试: {case['name']}")
            
            try:
                await self.speech_service.transcribe_audio(
                    case['data'],
                    format=case['format']
                )
                print("   ❌ 预期应该出现错误，但处理成功了")
                
            except ValueError as e:
                if case['expected_error'] in str(e):
                    print(f"   ✅ 正确捕获预期错误: {str(e)}")
                else:
                    print(f"   ⚠️  捕获了错误，但不是预期的: {str(e)}")
                    
            except Exception as e:
                print(f"   ❌ 捕获了意外错误: {str(e)}")
    
    async def run_all_examples(self):
        """运行所有示例"""
        print("🎤 语音识别和分析功能演示")
        print("=" * 50)
        
        try:
            await self.single_audio_analysis()
            await self.batch_audio_analysis()
            await self.audio_quality_validation()
            await self.language_support_demo()
            await self.error_handling_demo()
            
            print("\n🎉 语音分析演示完成！")
            print("\n✅ 演示的功能:")
            print("   • 单个音频文件识别和分析")
            print("   • 批量音频文件处理")
            print("   • 音频质量验证")
            print("   • 多语言支持")
            print("   • 错误处理机制")
            
        except Exception as e:
            print(f"❌ 演示过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

async def main():
    """主函数"""
    example = SpeechAnalysisExample()
    await example.run_all_examples()

if __name__ == "__main__":
    asyncio.run(main())