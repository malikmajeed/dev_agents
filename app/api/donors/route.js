import { NextResponse } from 'next/server';
import { verify } from 'jsonwebtoken';
import { z } from 'zod';
import donorService from '../../services/donorService.js';

// Zod schema for creating a donor
const createDonorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
});

/**
 * Verify JWT token from Authorization header.
 * Throws an error if token is missing or invalid.
 */
async function authenticate(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw { status: 401, message: 'Missing or malformed Authorization header' };
  }
  const token = authHeader.split(' ')[1];
  try {
    const payload = verify(token, process.env.JWT_SECRET);
    return payload; // payload can be used later if needed
  } catch (err) {
    throw { status: 401, message: 'Invalid or expired token' };
  }
}

export async function GET(request) {
  try {
    await authenticate(request);
    const donors = await donorService.getAllDonors();
    return NextResponse.json({ donors }, { status: 200 });
  } catch (err) {
    const status = err.status || 500;
    const message = err.message || 'Internal Server Error';
    return NextResponse.json({ error: message }, { status });
  }
}

export async function POST(request) {
  try {
    await authenticate(request);
    const body = await request.json();
    const parsed = createDonorSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { error: 'Validation failed', details: parsed.error.format() },
        { status: 400 }
      );
    }
    const newDonor = await donorService.createDonor(parsed.data);
    return NextResponse.json({ donor: newDonor }, { status: 201 });
  } catch (err) {
    const status = err.status || 500;
    const message = err.message || 'Internal Server Error';
    return NextResponse.json({ error: message }, { status });
  }
}
