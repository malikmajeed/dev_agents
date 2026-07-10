import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';
import { z } from 'zod';
import { getAllDonors, createDonor } from '@/services/donorService';

const JWT_SECRET = process.env.JWT_SECRET;

function verifyAuth(req) {
  const authHeader = req.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Missing or invalid Authorization header');
  }
  const token = authHeader.split(' ')[1];
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch (err) {
    throw new Error('Invalid token');
  }
}

const donorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
});

export async function GET(req) {
  try {
    verifyAuth(req);
    const donors = await getAllDonors();
    return NextResponse.json({ donors }, { status: 200 });
  } catch (error) {
    const status = error.message.includes('Authorization') ? 401 : 500;
    return NextResponse.json({ error: error.message }, { status });
  }
}

export async function POST(req) {
  try {
    verifyAuth(req);
    const body = await req.json();
    const parsed = donorSchema.parse(body);
    const donor = await createDonor(parsed);
    return NextResponse.json({ donor }, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.errors }, { status: 400 });
    }
    const status = error.message.includes('Authorization') ? 401 : 500;
    return NextResponse.json({ error: error.message }, { status });
  }
}
