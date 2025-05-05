# backend/app/test_db.py
import asyncio
from db import connect_db, close_db, insert_document, find_document, update_document, delete_document

async def main():
    # 1) Connect
    await connect_db()
    print("✅ Connected to MongoDB")

    # 2) Insert a test document
    data = { "test_field": "hello world" }
    doc_id = await insert_document("test_collection", data)
    print(f"✅ Inserted document with _id = {doc_id}")

    # 3) Read it back
    doc = await find_document("test_collection", {"_id": doc_id})
    print("✅ Retrieved document:", doc)

    # 4) Update it
    count = await update_document("test_collection", {"_id": doc_id}, {"test_field": "updated"})
    print(f"✅ Updated {count} document(s)")

    # 5) Verify update
    doc = await find_document("test_collection", {"_id": doc_id})
    print("✅ After update:", doc)

    # 6) Delete it
    deleted = await delete_document("test_collection", {"_id": doc_id})
    print(f"✅ Deleted {deleted} document(s)")

    # 7) Disconnect
    await close_db()
    print("✅ Closed MongoDB connection")

if __name__ == "__main__":
    asyncio.run(main())
