import { NextResponse } from 'next/server';
import { createDonor, getAllDonors } from '@/services/donorService';
import { z } from 'zod';
import jwt from 'jsonwebtoken';

// Zod schema for donor creation
const donorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
});

/**
 * Verify JWT token from Authorization header.
 * Returns the decoded payload if valid, otherwise throws.
 */
function verifyAuth(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Missing or malformed Authorization header');
  }
  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    return decoded;
  } catch (err) {
    throw new Error('Invalid or expired token');
  }
}

export async function GET(request) {
  try {
    // Authenticate admin user
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
    const body = await request.json();
    const parsed = donorSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { error: 'Invalid request data', details: parsed.error.format() },
        { status: 400 }
      );
    }

    const newDonor = await createDonor(parsed.data);
    return NextResponse.json({ donor: newDonor }, { status: 201 });
  } catch (error) {
    console.error('Error in POST /api/donors:', error);
    return NextResponse.json({ error: error.message || 'Server error' }, { status: 500 });
  }
}
