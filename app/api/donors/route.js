import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';
import { z } from 'zod';
import donorService from '@/services/donorService';

// Zod schema for creating a donor
const createDonorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
});

/**
 * Verify JWT token from Authorization header.
 * Returns the decoded payload if valid, otherwise throws.
 */
function verifyToken(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Missing or malformed Authorization header');
  }
  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    return decoded;
  } catch (err) {
    throw new Error('Invalid token');
  }
}

export async function GET(request) {
  try {
    // Ensure the request is authenticated
    verifyToken(request);

    const donors = await donorService.getAllDonors();
    return NextResponse.json(donors, { status: 200 });
  } catch (error) {
    const status = error.message.includes('Authorization') || error.message.includes('token') ? 401 : 500;
    return NextResponse.json({ error: error.message }, { status });
  }
}

export async function POST(request) {
  try {
    // Authenticate admin/user
    verifyToken(request);

    const body = await request.json();
    const parsed = createDonorSchema.safeParse(body);
    if (!parsed.success) {
      const errors = parsed.error.errors.map((e) => e.message);
      return NextResponse.json({ error: 'Validation failed', details: errors }, { status: 400 });
    }

    const newDonor = await donorService.createDonor(parsed.data);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (error) {
    const status = error.message.includes('Authorization') || error.message.includes('token') ? 401 : 500;
    return NextResponse.json({ error: error.message }, { status });
  }
}
