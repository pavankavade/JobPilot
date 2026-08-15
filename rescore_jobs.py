import database
import job_matcher

def rescore():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs")
    rows = cursor.fetchall()
    print(f"[*] Re-scoring {len(rows)} jobs in database with AI & Architecture priority...")

    updated_count = 0
    for r in rows:
        job = dict(r)
        score_data = job_matcher.calculate_match_score(job)
        new_score = score_data["match_score"]
        cursor.execute("UPDATE jobs SET match_score = ? WHERE id = ?", (new_score, job["id"]))
        updated_count += 1

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Re-scored {updated_count} jobs!")

    top_jobs = database.get_jobs()[:10]
    print("\n--- TOP RANKED AI & ARCHITECT ROLES ---")
    for idx, j in enumerate(top_jobs, start=1):
        print(f"{idx}. [{j['match_score']}% Match] [{j['portal']}] {j['title']} ({j['company']})")

if __name__ == "__main__":
    rescore()
