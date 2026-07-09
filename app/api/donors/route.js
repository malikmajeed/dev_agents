import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';
import { getAllDonors, createDonor } from '@/services/donorService';

const JWT_SECRET = process.env.JWT_SECRET;

function verifyToken(req) {
  const authHeader = req.headers.get('authorization');
  if (!authHeader) {
    throw new Error('Missing Authorization header');
  }
  const token = authHeader.split(' ')[1];
  if (!token) {
    throw new Error('Invalid Authorization header');
  }
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch (err) {
    throw new Error('Invalid token');
  }
}

export async function GET(req) {
  try {
    verifyToken(req);
    const donors = await getAllDonors();
    return NextResponse.json(donors);
  } catch (err) {
    const status = err.message.includes('Authorization') || err.message.includes('token') ? 401 : 500;
    return NextResponse.json({ error: err.message }, { status });
  }
}

export async function POST(req) {
  try {
    verifyToken(req);
    const body = await req.json();
    const newDonor = await createDonor(body);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (err) {
    const status = err.message.includes('validation') ? 400 : 401;
    return NextResponse.json({ error: err.message }, { status });
  }
}
