import { NextResponse } from 'next/server';
import { z } from 'zod';
import jwt from 'jsonwebtoken';
import { getAllDonors, createDonor } from '@/services/donorService';

// ---------------------------------------------------
// Helper: verify JWT token (expects Bearer token)
// ---------------------------------------------------
const verifyAuth = (request) => {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null;
  }
  const token = authHeader.split(' ')[1];
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);
    return payload; // could contain user id, role, etc.
  } catch (err) {
    return null;
  }
};

// ---------------------------------------------------
// Validation schema for creating a donor
// ---------------------------------------------------
const donorCreateSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email'),
  phone: z.string().optional(),
  address: z.string().optional(),
});

// ---------------------------------------------------
// GET /api/donors – list all donors (admin only)
// ---------------------------------------------------
export async function GET(request) {
  const user = verifyAuth(request);
  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const donors = await getAllDonors();
    return NextResponse.json(donors);
  } catch (error) {
    console.error('Error fetching donors:', error);
    return NextResponse.json({ error: 'Failed to fetch donors' }, { status: 500 });
  }
}

// ---------------------------------------------------
// POST /api/donors – create a new donor (admin only)
// ---------------------------------------------------
export async function POST(request) {
  const user = verifyAuth(request);
  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  let body;
  try {
    body = await request.json();
  } catch (err) {
    return NextResponse.json({ error: 'Invalid JSON payload' }, { status: 400 });
  }

  const parseResult = donorCreateSchema.safeParse(body);
  if (!parseResult.success) {
    return NextResponse.json({ error: 'Validation failed', details: parseResult.error.format() }, { status: 400 });
  }

  try {
    const newDonor = await createDonor(parseResult.data);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (error) {
    console.error('Error creating donor:', error);
    return NextResponse.json({ error: 'Failed to create donor' }, { status: 500 });
  }
}
