#!/usr/bin/env python3
"""
Test script to verify header detection and data loading fixes
"""

import sys
import os
import tempfile

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_data_with_headers():
    """Create test data files - one with headers, one without"""
    
    # Test data with headers
    header_data = """distance_0,distance_1,distance_2,distance_3,distance_4,distance_5,distance_6,distance_7,distance_8,distance_9,distance_10,distance_11,distance_12,distance_13,distance_14,distance_15,distance_16,distance_17,distance_18,distance_19,distance_20,distance_21,distance_22,distance_23,distance_24,distance_25,distance_26,distance_27,distance_28,distance_29,distance_30,distance_31,distance_32,distance_33,distance_34,distance_35,distance_36,distance_37,distance_38,distance_39,distance_40,distance_41,distance_42,distance_43,distance_44,distance_45,distance_46,distance_47,distance_48,distance_49,distance_50,distance_51,distance_52,distance_53,distance_54,distance_55,distance_56,distance_57,distance_58,distance_59,distance_60,distance_61,distance_62,distance_63,distance_64,distance_65,distance_66,distance_67,distance_68,distance_69,distance_70,distance_71,distance_72,distance_73,distance_74,distance_75,distance_76,distance_77,distance_78,distance_79,distance_80,distance_81,distance_82,distance_83,distance_84,distance_85,distance_86,distance_87,distance_88,distance_89,distance_90,distance_91,distance_92,distance_93,distance_94,distance_95,distance_96,distance_97,distance_98,distance_99,distance_100,distance_101,distance_102,distance_103,distance_104,distance_105,distance_106,distance_107,distance_108,distance_109,distance_110,distance_111,distance_112,distance_113,distance_114,distance_115,distance_116,distance_117,distance_118,distance_119,distance_120,distance_121,distance_122,distance_123,distance_124,distance_125,distance_126,distance_127,distance_128,distance_129,distance_130,distance_131,distance_132,distance_133,distance_134,distance_135,distance_136,distance_137,distance_138,distance_139,distance_140,distance_141,distance_142,distance_143,distance_144,distance_145,distance_146,distance_147,distance_148,distance_149,distance_150,distance_151,distance_152,distance_153,distance_154,distance_155,distance_156,distance_157,distance_158,distance_159,distance_160,distance_161,distance_162,distance_163,distance_164,distance_165,distance_166,distance_167,distance_168,distance_169,distance_170,distance_171,distance_172,distance_173,distance_174,distance_175,distance_176,distance_177,distance_178,distance_179,distance_180,distance_181,distance_182,distance_183,distance_184,distance_185,distance_186,distance_187,distance_188,distance_189,distance_190,distance_191,distance_192,distance_193,distance_194,distance_195,distance_196,distance_197,distance_198,distance_199,distance_200,distance_201,distance_202,distance_203,distance_204,distance_205,distance_206,distance_207,distance_208,distance_209,distance_210,distance_211,distance_212,distance_213,distance_214,distance_215,distance_216,distance_217,distance_218,distance_219,distance_220,distance_221,distance_222,distance_223,distance_224,distance_225,distance_226,distance_227,distance_228,distance_229,distance_230,distance_231,distance_232,distance_233,distance_234,distance_235,distance_236,distance_237,distance_238,distance_239,distance_240,distance_241,distance_242,distance_243,distance_244,distance_245,distance_246,distance_247,distance_248,distance_249,distance_250,distance_251,distance_252,distance_253,distance_254,distance_255,distance_256,distance_257,distance_258,distance_259,distance_260,distance_261,distance_262,distance_263,distance_264,distance_265,distance_266,distance_267,distance_268,distance_269,distance_270,distance_271,distance_272,distance_273,distance_274,distance_275,distance_276,distance_277,distance_278,distance_279,distance_280,distance_281,distance_282,distance_283,distance_284,distance_285,distance_286,distance_287,distance_288,distance_289,distance_290,distance_291,distance_292,distance_293,distance_294,distance_295,distance_296,distance_297,distance_298,distance_299,distance_300,distance_301,distance_302,distance_303,distance_304,distance_305,distance_306,distance_307,distance_308,distance_309,distance_310,distance_311,distance_312,distance_313,distance_314,distance_315,distance_316,distance_317,distance_318,distance_319,distance_320,distance_321,distance_322,distance_323,distance_324,distance_325,distance_326,distance_327,distance_328,distance_329,distance_330,distance_331,distance_332,distance_333,distance_334,distance_335,distance_336,distance_337,distance_338,distance_339,distance_340,distance_341,distance_342,distance_343,distance_344,distance_345,distance_346,distance_347,distance_348,distance_349,distance_350,distance_351,distance_352,distance_353,distance_354,distance_355,distance_356,distance_357,distance_358,distance_359,angular_velocity
500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,-0.5
450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,0.3"""
    
    # Test data without headers
    no_header_data = """500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,500.0,600.0,700.0,800.0,-0.5
450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,450.0,550.0,650.0,750.0,0.3"""
    
    # Create temporary files
    header_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    no_header_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    
    header_file.write(header_data)
    header_file.flush()
    
    no_header_file.write(no_header_data)
    no_header_file.flush()
    
    return header_file.name, no_header_file.name

def test_header_detection():
    """Test the header detection functionality"""
    print("Testing header detection...")
    
    try:
        from pginput import DataManager
        import tempfile
        
        header_file, no_header_file = create_test_data_with_headers()
        
        print(f"Created test files:")
        print(f"  With headers: {header_file}")
        print(f"  Without headers: {no_header_file}")
        
        # Test file with headers
        print(f"\nTesting file WITH headers...")
        temp_output = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_output.close()
        
        dm_header = DataManager(header_file, temp_output.name, False)
        
        if hasattr(dm_header, '_header_detected'):
            print(f"✓ Header detection: {dm_header._header_detected}")
            print(f"✓ Data start line: {dm_header._data_start_line}")
            print(f"✓ Starting pointer: {dm_header.pointer}")
            
            # Test reading first data frame
            first_frame = dm_header.dataframe
            print(f"✓ First frame length: {len(first_frame)}")
            
            # Try to convert first few values to float (should work now)
            try:
                float_vals = [float(first_frame[i]) for i in range(5)]
                print(f"✓ First 5 values as floats: {float_vals}")
            except ValueError as e:
                print(f"✗ Failed to convert values to float: {e}")
                return False
        else:
            print(f"✗ Header detection not implemented")
            return False
        
        # Test file without headers
        print(f"\nTesting file WITHOUT headers...")
        temp_output2 = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_output2.close()
        
        dm_no_header = DataManager(no_header_file, temp_output2.name, False)
        
        if hasattr(dm_no_header, '_header_detected'):
            print(f"✓ Header detection: {dm_no_header._header_detected}")
            print(f"✓ Data start line: {dm_no_header._data_start_line}")
            print(f"✓ Starting pointer: {dm_no_header.pointer}")
            
            # Test reading first data frame
            first_frame = dm_no_header.dataframe
            print(f"✓ First frame length: {len(first_frame)}")
            
            # Try to convert first few values to float
            try:
                float_vals = [float(first_frame[i]) for i in range(5)]
                print(f"✓ First 5 values as floats: {float_vals}")
            except ValueError as e:
                print(f"✗ Failed to convert values to float: {e}")
                return False
        
        # Cleanup
        os.unlink(header_file)
        os.unlink(no_header_file)
        os.unlink(temp_output.name)
        os.unlink(temp_output2.name)
        
        print("✓ Header detection test passed")
        return True
        
    except Exception as e:
        print(f"✗ Header detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scale_factor_calculation():
    """Test that scale factor calculation works with header detection"""
    print("\nTesting scale factor calculation...")
    
    try:
        from pginput import DataManager
        from main import calculate_scale_factor
        import tempfile
        
        header_file, no_header_file = create_test_data_with_headers()
        
        # Test with headers
        print("Testing scale factor with headers...")
        temp_output = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_output.close()
        
        dm_header = DataManager(header_file, temp_output.name, False)
        scale_factor = calculate_scale_factor(dm_header, sample_size=2)
        
        print(f"✓ Scale factor calculated: {scale_factor:.4f}")
        
        # Test with no headers
        print("Testing scale factor without headers...")
        temp_output2 = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_output2.close()
        
        dm_no_header = DataManager(no_header_file, temp_output2.name, False)
        scale_factor2 = calculate_scale_factor(dm_no_header, sample_size=2)
        
        print(f"✓ Scale factor calculated: {scale_factor2:.4f}")
        
        # Both should produce valid scale factors
        if scale_factor > 0 and scale_factor2 > 0:
            print("✓ Scale factor calculation works with both header types")
            result = True
        else:
            print("✗ Invalid scale factors calculated")
            result = False
        
        # Cleanup
        os.unlink(header_file)
        os.unlink(no_header_file)
        os.unlink(temp_output.name)
        os.unlink(temp_output2.name)
        
        return result
        
    except Exception as e:
        print(f"✗ Scale factor calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Header Detection Bug Fix Test ===\n")
    
    # Test header detection
    header_test = test_header_detection()
    
    # Test scale factor calculation
    scale_test = test_scale_factor_calculation()
    
    print(f"\n=== Test Results ===")
    print(f"Header detection: {'✓ PASS' if header_test else '✗ FAIL'}")
    print(f"Scale factor calculation: {'✓ PASS' if scale_test else '✗ FAIL'}")
    
    if header_test and scale_test:
        print("\n🎉 Header detection bug fix successful!")
        print("\nFixes implemented:")
        print("  - Added _detect_header() method to DataManager")
        print("  - DataManager now automatically skips header rows")
        print("  - Navigation methods respect data start line")
        print("  - calculate_scale_factor() uses correct data start line")
        print("  - Both monolithic and modular versions now handle headers")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        sys.exit(1)
