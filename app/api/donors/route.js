import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';
import { getAllDonors, createDonor } from '@/services/donorService';
import { z } from 'zod';

const JWT_SECRET = process.env.JWT_SECRET;

function verifyAuth(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw { status: 401, message: 'Missing or malformed Authorization header' };
  }
  const token = authHeader.split(' ')[1];
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch (err) {
    throw { status: 401, message: 'Invalid or expired token' };
  }
}

export async function GET(request) {
  try {
    verifyAuth(request);
    const donors = await getAllDonors();
    return NextResponse.json({ donors });
  } catch (error) {
    const status = error.status || 500;
    const message = error.message || 'Internal Server Error';
    return NextResponse.json({ error: message }, { status });
  }
}

export async function POST(request) {
  try {
    verifyAuth(request);
    const body = await request.json();
    const donorSchema = z.object({
      name: z.string().min(1),
      email: z.string().email(),
      phone: z.string().optional(),
      address: z.string().optional()
    });
    const parsedData = donorSchema.parse(body);
    const donor = await createDonor(parsedData);
    return NextResponse.json({ donor }, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.errors }, { status: 400 });
    }
    const status = error.status || 500;
    const message = error.message || 'Internal Server Error';
    return NextResponse.json({ error: message }, { status });
  }
}
