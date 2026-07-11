import { NextResponse } from 'next/server';
import { getAllDonors, createDonor } from '@/services/donorService';
import { z } from 'zod';
import jwt from 'jsonwebtoken';

// Helper to verify JWT and return payload
function verifyAuth(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader) {
    throw new Error('Missing Authorization header');
  }
  const parts = authHeader.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') {
    throw new Error('Invalid Authorization format');
  }
  const token = parts[1];
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);
    return payload;
  } catch (err) {
    // Re‑throw to be caught in the route handler
    throw err;
  }
}

/**
 * GET /api/donors
 * Returns a list of all donors. Protected – requires a valid JWT.
 */
export async function GET(request) {
  try {
    // Auth check
    verifyAuth(request);

    const donors = await getAllDonors();
    return NextResponse.json(donors);
  } catch (error) {
    if (error.name === 'JsonWebTokenError' || error.name === 'TokenExpiredError') {
      return NextResponse.json({ error: 'Invalid or expired token' }, { status: 401 });
    }
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
  }
}

/**
 * POST /api/donors
 * Creates a new donor record. Protected – requires a valid JWT.
 * Expected body: { name, email, phone?, address? }
 */
export async function POST(request) {
  try {
    // Auth check
    verifyAuth(request);

    const body = await request.json();
    const donorSchema = z.object({
      name: z.string().min(1, 'Name is required'),
      email: z.string().email('Invalid email address'),
      phone: z.string().optional(),
      address: z.string().optional()
    });
    const validatedData = donorSchema.parse(body);

    const newDonor = await createDonor(validatedData);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.errors }, { status: 400 });
    }
    if (error.name === 'JsonWebTokenError' || error.name === 'TokenExpiredError') {
      return NextResponse.json({ error: 'Invalid or expired token' }, { status: 401 });
    }
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
  }
}
