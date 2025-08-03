#!/usr/bin/env python3
"""
Test script to verify the frame navigation bug fix for the next/prev issue
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pginput import DataManager

def test_next_prev_navigation_bug_fix():
    """Test that next->prev navigation returns to the original frame"""
    print("Testing Next/Prev Frame Navigation Bug Fix")
    print("=" * 50)
    
    # Create test data file
    test_file = "/tmp/test_navigation.csv"
    test_data = """# Header line
0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,0.1
1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,0.2
2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,0.3"""
    
    with open(test_file, 'w') as f:
        f.write(test_data)
    
    # Initialize DataManager with test file
    dm = DataManager(test_file, "/tmp/test_out.csv")
    
    print(f"Initial state:")
    print(f"  Pointer: {dm._pointer}")
    print(f"  Read pos: {dm._read_pos}")
    print(f"  Dataframe length: {len(dm.dataframe)}")
    print(f"  Current frame angular velocity: {dm.dataframe[-1] if len(dm.dataframe) > 0 else 'N/A'}")  # Last element is angular velocity
    
    # Save initial state
    initial_pointer = dm._pointer
    initial_angular = dm.dataframe[-1] if len(dm.dataframe) > 0 else 'N/A'
    
    print(f"\nStep 1: Move to next frame")
    dm.next()
    print(f"  Pointer: {dm._pointer}")
    print(f"  Read pos: {dm._read_pos}")
    print(f"  Dataframe length: {len(dm.dataframe)}")
    print(f"  Current frame angular velocity: {dm.dataframe[-1] if len(dm.dataframe) > 0 else 'N/A'}")
    
    next_pointer = dm._pointer
    next_angular = dm.dataframe[-1] if len(dm.dataframe) > 0 else 'N/A'
    
    print(f"\nStep 2: Move back to previous frame")
    dm.prev()
    print(f"  Pointer: {dm._pointer}")
    print(f"  Read pos: {dm._read_pos}")
    print(f"  Dataframe length: {len(dm.dataframe)}")
    print(f"  Current frame angular velocity: {dm.dataframe[-1] if len(dm.dataframe) > 0 else 'N/A'}")
    
    final_pointer = dm._pointer
    final_angular = dm.dataframe[-1] if len(dm.dataframe) > 0 else 'N/A'
    
    # Verify the fix
    print(f"\n" + "=" * 50)
    print("VERIFICATION RESULTS:")
    print(f"Initial pointer: {initial_pointer}, Angular velocity: {initial_angular}")
    print(f"After next pointer: {next_pointer}, Angular velocity: {next_angular}")
    print(f"After prev pointer: {final_pointer}, Angular velocity: {final_angular}")
    
    if initial_pointer == final_pointer and initial_angular == final_angular:
        print("✅ SUCCESS: Frame navigation works correctly!")
        print("   User correctly returns to the original frame after next->prev")
        return True
    else:
        print("❌ FAILURE: Frame navigation bug persists!")
        print("   User does not return to the original frame after next->prev")
        return False


def test_real_scenario():
    """Test the specific scenario described by the user: frame_1 -> next -> prev should return to frame_1"""
    print("\nTesting Real User Scenario")
    print("=" * 50)
    
    # Create test data file with data frames (skip header)  
    test_file = "/tmp/test_real_scenario.csv"
    test_data = """# Header line
100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,0.5
200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,0.8
300,301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,360,361,362,363,364,365,366,367,368,369,370,371,372,373,374,375,376,377,378,379,380,381,382,383,384,385,386,387,388,389,390,391,392,393,394,395,396,397,398,399,400,401,402,403,404,405,406,407,408,409,410,411,412,413,414,415,416,417,418,419,420,421,422,423,424,425,426,427,428,429,430,431,432,433,434,435,436,437,438,439,440,441,442,443,444,445,446,447,448,449,450,451,452,453,454,455,456,457,458,459,1.2"""
    
    with open(test_file, 'w') as f:
        f.write(test_data)
    
    # Initialize DataManager with test file
    dm = DataManager(test_file, "/tmp/test_real_out.csv")
    
    # Start at the first data frame (frame_1)
    print(f"User starts at Frame 1:")
    print(f"  Global pointer: {dm._pointer} (frame {dm._pointer + 1})")
    print(f"  Angular velocity: {dm.dataframe[-1]}")
    
    frame1_pointer = dm._pointer
    frame1_angular = dm.dataframe[-1]
    
    # User clicks "next"
    print(f"\nUser clicks 'Next':")
    dm.next()
    print(f"  Global pointer: {dm._pointer} (frame {dm._pointer + 1})")
    print(f"  Angular velocity: {dm.dataframe[-1]}")
    print(f"  _read_pos: {dm._read_pos}")
    
    frame2_pointer = dm._pointer
    frame2_angular = dm.dataframe[-1]
    
    # User clicks "prev"
    print(f"\nUser clicks 'Prev':")  
    dm.prev()
    print(f"  Global pointer: {dm._pointer} (frame {dm._pointer + 1})")
    print(f"  Angular velocity: {dm.dataframe[-1]}")
    print(f"  _read_pos: {dm._read_pos}")
    
    final_pointer = dm._pointer
    final_angular = dm.dataframe[-1]
    
    # Verify the fix
    print(f"\n" + "=" * 50)
    print("USER SCENARIO VERIFICATION:")
    print(f"Started at Frame {frame1_pointer + 1}: Angular velocity = {frame1_angular}")
    print(f"Moved to Frame {frame2_pointer + 1}: Angular velocity = {frame2_angular}")
    print(f"Returned to Frame {final_pointer + 1}: Angular velocity = {final_angular}")
    
    if frame1_pointer == final_pointer and frame1_angular == final_angular:
        print("✅ SUCCESS: User correctly returns to Frame 1 after next->prev")
        return True
    else:
        print("❌ FAILURE: User does NOT return to Frame 1 after next->prev")
        print(f"   Expected: Frame {frame1_pointer + 1}, Got: Frame {final_pointer + 1}")
        return False

if __name__ == "__main__":
    success1 = test_next_prev_navigation_bug_fix()
    success2 = test_real_scenario()
    
    print(f"\n" + "=" * 60)
    print("FINAL SUMMARY:")
    print(f"Basic next/prev test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Real user scenario test: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED! The frame navigation bug has been fixed.")
        print("Users can now navigate frame_1 -> next -> prev and return to frame_1 correctly.")
    else:
        print("\n⚠️  SOME TESTS FAILED! The bug may still exist.")
    
    sys.exit(0 if (success1 and success2) else 1)
