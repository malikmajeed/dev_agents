import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';
import { getAllDonors, createDonor } from '@/services/donorService';
import { z } from 'zod';

// Validation schema for creating a donor
const donorCreateSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
});

// Simple JWT auth helper – throws on failure
function verifyAuth(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Missing or invalid Authorization header');
  }
  const token = authHeader.split(' ')[1];
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);
    return payload; // payload can be used later if needed
  } catch (err) {
    throw new Error('Invalid token');
  }
}

export async function GET(request) {
  try {
    // Ensure the caller is authenticated (admin staff)
    verifyAuth(request);
    const donors = await getAllDonors();
    return NextResponse.json(donors);
  } catch (err) {
    const status = err.message.includes('Authorization') ? 401 : 500;
    return NextResponse.json({ error: err.message }, { status });
  }
}

export async function POST(request) {
  try {
    verifyAuth(request);
    const body = await request.json();
    const validated = donorCreateSchema.parse(body);
    const newDonor = await createDonor(validated);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (err) {
    if (err.name === 'ZodError') {
      return NextResponse.json({ error: err.errors }, { status: 400 });
    }
    const status = err.message.includes('Authorization') ? 401 : 500;
    return NextResponse.json({ error: err.message }, { status });
  }
}
