import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';
import { getAllDonors, createDonor } from '../../services/donorService';
import { z } from 'zod';

// Validation schema for creating a donor
const donorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
});

/**
 * Verify JWT token from Authorization header.
 * Throws an error if token is missing or invalid.
 */
function verifyToken(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Missing or malformed Authorization header');
  }
  const token = authHeader.split(' ')[1];
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);
    return payload;
  } catch (err) {
    throw new Error('Invalid token');
  }
}

export async function GET(request) {
  try {
    // Ensure request is authenticated
    verifyToken(request);

    const donors = await getAllDonors();
    return NextResponse.json(donors);
  } catch (err) {
    const status = err.message.includes('Authorization') || err.message.includes('Invalid token') ? 401 : 500;
    return NextResponse.json({ error: err.message }, { status });
  }
}

export async function POST(request) {
  try {
    // Authentication
    verifyToken(request);

    const body = await request.json();
    const validated = donorSchema.parse(body);

    const newDonor = await createDonor(validated);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (err) {
    if (err instanceof z.ZodError) {
      return NextResponse.json({ error: err.errors }, { status: 400 });
    }
    const status = err.message.includes('Authorization') || err.message.includes('Invalid token') ? 401 : 500;
    return NextResponse.json({ error: err.message }, { status });
  }
}
