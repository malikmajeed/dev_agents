import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import { z } from 'zod';
import { getAllDonors, createDonor } from '@/services/donorService';

// Validation schema for creating a donor
const donorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  password: z.string().min(6, { message: 'Password must be at least 6 characters' }),
  address: z.string().optional(),
  phone: z.string().optional(),
});

// Helper to extract Bearer token from Authorization header
function getToken(req) {
  const authHeader = req.headers.get('authorization');
  if (!authHeader) return null;
  const parts = authHeader.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') return null;
  return parts[1];
}

export async function GET(req) {
  try {
    const token = getToken(req);
    if (!token) {
      return NextResponse.json({ error: 'Missing or malformed token' }, { status: 401 });
    }
    const secret = process.env.JWT_SECRET;
    jwt.verify(token, secret);
    const donors = await getAllDonors();
    return NextResponse.json(donors);
  } catch (err) {
    const status = err.name === 'JsonWebTokenError' || err.name === 'TokenExpiredError' ? 401 : 500;
    return NextResponse.json({ error: err.message }, { status });
  }
}

export async function POST(req) {
  try {
    const body = await req.json();
    const result = donorSchema.safeParse(body);
    if (!result.success) {
      return NextResponse.json({ error: result.error.errors }, { status: 400 });
    }
    const { name, email, password, address, phone } = result.data;
    const hashedPassword = await bcrypt.hash(password, 10);
    const newDonor = await createDonor({
      name,
      email,
      password: hashedPassword,
      address,
      phone,
    });
    return NextResponse.json(newDonor, { status: 201 });
  } catch (err) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
