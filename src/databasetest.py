connect = "postgresql://neondb_owner:npg_Te8KnPXpq9Yr@ep-lingering-lab-aevc8697-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

import psycopg2
from datetime import date

# Replace with your Neon connection string
CONN_STR = connect

def main():
    try:
        # Connect to the database
        conn = psycopg2.connect(CONN_STR)
        cur = conn.cursor()

        # Insert a sample record
        insert_query = """
        INSERT INTO specs (lot_id, description, start_date, end_date, creation_date)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """

        data = (
            "LOT123",
            "Test description",
            date(2026, 4, 19),
            date(2026, 5, 1),
            date.today()
        )

        cur.execute(insert_query, data)
        new_id = cur.fetchone()[0]
        print(f"Inserted row with id: {new_id}")

        # Commit the transaction
        conn.commit()

        # Query all rows
        cur.execute("SELECT * FROM specs;")
        rows = cur.fetchall()

        print("\nCurrent contents of 'specs':")
        for row in rows:
            print(row)

        # Cleanup
        cur.close()
        conn.close()

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()