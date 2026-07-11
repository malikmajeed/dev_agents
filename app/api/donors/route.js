import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';
import { z } from 'zod';
import { getDonors, createDonor } from '@/services/donorService';

/**
 * GET /api/donors
 * Returns a list of all donors.
 */
export async function GET(request) {
  try {
    const donors = await getDonors();
    return NextResponse.json(donors);
  } catch (error) {
    console.error('Error fetching donors:', error);
    return NextResponse.json(
      { error: 'Failed to fetch donors' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/donors
 * Creates a new donor. Requires a valid JWT in the Authorization header.
 */
export async function POST(request) {
  // ---- Authentication ----
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'Missing or malformed Authorization header' }, { status: 401 });
  }
  const token = authHeader.split(' ')[1];
  try {
    jwt.verify(token, process.env.JWT_SECRET);
  } catch (err) {
    return NextResponse.json({ error: 'Invalid or expired token' }, { status: 401 });
  }

  // ---- Validation ----
  const body = await request.json();
  const donorSchema = z.object({
    name: z.string().min(1, { message: 'Name is required' }),
    email: z.string().email({ message: 'Invalid email address' }),
    phone: z.string().optional(),
    address: z.string().optional(),
  });

  try {
    const validatedData = donorSchema.parse(body);
    const newDonor = await createDonor(validatedData);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (err) {
    console.error('Error creating donor:', err);
    if (err instanceof z.ZodError) {
      return NextResponse.json({ error: err.errors }, { status: 400 });
    }
    return NextResponse.json({ error: 'Failed to create donor' }, { status: 500 });
  }
}
