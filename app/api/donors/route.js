import { NextResponse } from 'next/server';
import { verify } from 'jsonwebtoken';
import { z } from 'zod';
import { getAllDonors, createDonor } from '@/services/donorService';

// Validation schema for creating a donor
const donorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
});

// Helper to verify JWT token
function verifyToken(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Missing or malformed Authorization header');
  }
  const token = authHeader.split(' ')[1];
  const secret = process.env.JWT_SECRET;
  if (!secret) {
    throw new Error('JWT secret not configured');
  }
  try {
    return verify(token, secret);
  } catch (err) {
    throw new Error('Invalid token');
  }
}

export async function GET(request) {
  try {
    // Authenticate admin/user
    verifyToken(request);

    const donors = await getAllDonors();
    return NextResponse.json({ success: true, data: donors }, { status: 200 });
  } catch (error) {
    const message = error.message || 'Internal Server Error';
    const status = message.includes('Authorization') || message.includes('token') ? 401 : 500;
    return NextResponse.json({ success: false, error: message }, { status });
  }
}

export async function POST(request) {
  try {
    // Authenticate admin/user
    verifyToken(request);

    const body = await request.json();
    const validated = donorSchema.parse(body);

    const newDonor = await createDonor(validated);
    return NextResponse.json({ success: true, data: newDonor }, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, error: error.errors.map((e) => e.message) },
        { status: 400 }
      );
    }
    const message = error.message || 'Internal Server Error';
    const status = message.includes('Authorization') || message.includes('token') ? 401 : 500;
    return NextResponse.json({ success: false, error: message }, { status });
  }
}
