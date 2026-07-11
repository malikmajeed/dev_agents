import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';
import { z } from 'zod';
import donorService from '@/services/donorService';

// Zod schema for creating a donor
const createDonorSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  phone: z.string().optional(),
  address: z.string().optional(),
});

// Helper to verify JWT and extract payload
function verifyAuth(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Missing or malformed Authorization header');
  }
  const token = authHeader.split(' ')[1];
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);
    return payload;
  } catch (err) {
    throw new Error('Invalid or expired token');
  }
}

export async function GET(request) {
  try {
    // Optional: protect the route – only admins can list donors
    verifyAuth(request);
    const donors = await donorService.getAllDonors();
    return NextResponse.json(donors);
  } catch (error) {
    const status = error.message.includes('Authorization') ? 401 : 500;
    return NextResponse.json({ error: error.message }, { status });
  }
}

export async function POST(request) {
  try {
    // Protect route – only authenticated admins can create donors
    verifyAuth(request);
    const body = await request.json();
    const parsed = createDonorSchema.parse(body);
    const newDonor = await donorService.createDonor(parsed);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.errors }, { status: 400 });
    }
    const status = error.message.includes('Authorization') ? 401 : 500;
    return NextResponse.json({ error: error.message }, { status });
  }
}
