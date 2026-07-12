import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';
import { z } from 'zod';
import { getAllDonors, createDonor } from '@/services/donorService';

// Zod schema for donor creation
const donorSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email address'),
  phone: z.string().optional(),
  address: z.string().optional(),
});

// Helper to verify JWT token
function verifyAuth(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Missing or malformed Authorization header');
  }
  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    return decoded; // payload can be used later if needed
  } catch (err) {
    throw new Error('Invalid or expired token');
  }
}

export async function GET(request) {
  try {
    // Authenticate admin/staff
    verifyAuth(request);

    const donors = await getAllDonors();
    return NextResponse.json({ donors }, { status: 200 });
  } catch (error) {
    const status = error.message.includes('Authorization') ? 401 : 500;
    return NextResponse.json({ error: error.message }, { status });
  }
}

export async function POST(request) {
  try {
    // Authenticate admin/staff
    verifyAuth(request);

    const body = await request.json();
    const parsed = donorSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json({ error: parsed.error.errors }, { status: 400 });
    }

    const newDonor = await createDonor(parsed.data);
    return NextResponse.json({ donor: newDonor }, { status: 201 });
  } catch (error) {
    const status = error.message.includes('Authorization') ? 401 : 500;
    return NextResponse.json({ error: error.message }, { status });
  }
}
