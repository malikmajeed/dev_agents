import { NextResponse } from 'next/server';
import { verify } from 'jsonwebtoken';
import { z } from 'zod';
import { createDonor, getAllDonors } from '../../services/donorService.js';

// Zod schema for donor creation (public donation)
const donorCreateSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email'),
  amount: z.number().positive('Amount must be positive'),
  causeId: z.number().int().positive('Cause ID must be a positive integer'),
  message: z.string().optional(),
});

/**
 * GET /api/donors
 * Returns list of all donors (admin only)
 */
export async function GET(request) {
  try {
    const authHeader = request.headers.get('authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json({ error: 'Missing or malformed Authorization header' }, { status: 401 });
    }
    const token = authHeader.split(' ')[1];
    const secret = process.env.JWT_SECRET;
    if (!secret) {
      return NextResponse.json({ error: 'Server configuration error' }, { status: 500 });
    }
    try {
      verify(token, secret);
    } catch (err) {
      return NextResponse.json({ error: 'Invalid token' }, { status: 401 });
    }

    const donors = await getAllDonors();
    return NextResponse.json(donors);
  } catch (error) {
    console.error('GET /api/donors error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

/**
 * POST /api/donors
 * Create a new donor record (public donation)
 */
export async function POST(request) {
  try {
    const json = await request.json();
    const parsed = donorCreateSchema.safeParse(json);
    if (!parsed.success) {
      return NextResponse.json({ error: 'Invalid request data', details: parsed.error.format() }, { status: 400 });
    }
    const donorData = parsed.data;
    const newDonor = await createDonor(donorData);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (error) {
    console.error('POST /api/donors error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
