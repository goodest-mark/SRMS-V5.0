"""
Calls compute_student_scores() directly with exam_id=1, bypassing all UI code,
to prove whether the engine itself works. Run:

    python test_ranking_direct.py
"""
from ranking_engine import compute_student_scores

for class_name in ["Form I", "Form II", "Form III", "Form IV"]:
    result = compute_student_scores("O_LEVEL", exam_id=1, class_name=class_name, stream=None)
    print(f"{class_name}: {len(result)} students returned")
    if result:
        sample = result[0]
        print(f"   sample: {sample.get('name')} | position={sample.get('position')} "
              f"| total={sample.get('total_marks')} | status={sample.get('status')}")
    else:
        print("   -> EMPTY. Engine itself returns nothing for this class.")
    print()
