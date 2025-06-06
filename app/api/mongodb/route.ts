import { NextResponse } from 'next/server';
import { MongoClient } from 'mongodb';

const uri = 'mongodb+srv://jefino9488:Jefino1537@truthguardcluster.2wku5ai.mongodb.net/?retryWrites=true&w=majority&appName=TruthGuardCluster';
const dbName = 'truthguard';

export async function GET(request: Request) {
  if (!uri) return NextResponse.json({ error: 'Missing MONGODB_URI' }, { status: 500 });
  const client = new MongoClient(uri);
  try {
    await client.connect();
    const db = client.db(dbName);
    const collection = db.collection('articles');
    // Optionally, filter or limit results
    const articles = await collection.find({ processing_status: 'analyzed' }).sort({ published_at: -1 }).limit(50).toArray();
    return NextResponse.json({ articles });
  } catch (e) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  } finally {
    await client.close();
  }
}

