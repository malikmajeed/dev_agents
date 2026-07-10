import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';
import { z } from 'zod';
import { getAllDonors, createDonor } from '../../../services/donorService';

// Zod schema for donor creation
const donorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
});

// Helper to verify JWT and extract payload
function verifyAuth(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw { status: 401, message: 'Missing or malformed Authorization header' };
  }
  const token = authHeader.split(' ')[1];
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);
    return payload;
  } catch (err) {
    throw { status: 401, message: 'Invalid or expired token' };
  }
}

export async function GET(request) {
  try {
    // Ensure the request is authenticated
    verifyAuth(request);

    const donors = await getAllDonors();
    return NextResponse.json(donors, { status: 200 });
  } catch (err) {
    const status = err.status || 500;
    const message = err.message || 'Internal Server Error';
    return NextResponse.json({ error: message }, { status });
  }
}

export async function POST(request) {
  try {
    // Authenticate admin/staff
    verifyAuth(request);

    const body = await request.json();
    const parsed = donorSchema.safeParse(body);
    if (!parsed.success) {
      const errors = parsed.error.format();
      return NextResponse.json({ error: 'Validation failed', details: errors }, { status: 400 });
    }

    const newDonor = await createDonor(parsed.data);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (err) {
    const status = err.status || 500;
    const message = err.message || 'Internal Server Error';
    return NextResponse.json({ error: message }, { status });
  }
}
