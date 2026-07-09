import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';
import { createDonor, getAllDonors } from '../../../services/donorService';
import { z } from 'zod';

// Zod schema for donor creation
const donorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
});

// Helper to extract Bearer token from Authorization header
function getToken(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new jwt.JsonWebTokenError('Authorization token missing');
  }
  return authHeader.split(' ')[1];
}

// Verify JWT token using secret from env
function verifyToken(token) {
  const secret = process.env.JWT_SECRET;
  if (!secret) {
    throw new Error('JWT_SECRET is not defined in environment');
  }
  // jwt.verify throws on invalid token
  return jwt.verify(token, secret);
}

export async function GET(request) {
  try {
    const token = getToken(request);
    verifyToken(token);

    const donors = await getAllDonors();
    return NextResponse.json(donors, { status: 200 });
  } catch (error) {
    const status = error instanceof jwt.JsonWebTokenError ? 401 : 500;
    return NextResponse.json({ error: error.message }, { status });
  }
}

export async function POST(request) {
  try {
    const token = getToken(request);
    verifyToken(token);

    const body = await request.json();
    const validatedData = donorSchema.parse(body);

    const newDonor = await createDonor(validatedData);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.errors }, { status: 400 });
    }
    const status = error instanceof jwt.JsonWebTokenError ? 401 : 500;
    return NextResponse.json({ error: error.message }, { status });
  }
}
