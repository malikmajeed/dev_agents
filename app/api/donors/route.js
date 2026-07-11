import { NextResponse } from 'next/server';
import { verify } from 'jsonwebtoken';
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
 * Helper to extract and verify JWT from the Authorization header.
 * Throws an error if token is missing or invalid.
 */
async function getAuthenticatedUser(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader) {
    throw { status: 401, message: 'Authorization header missing' };
  }
  const parts = authHeader.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') {
    throw { status: 401, message: 'Invalid Authorization format' };
  }
  const token = parts[1];
  try {
    const payload = verify(token, process.env.JWT_SECRET);
    return payload; // payload can contain user id, role, etc.
  } catch (err) {
    throw { status: 401, message: 'Invalid or expired token' };
  }
}

/** GET /api/donors
 * Returns a list of all donors. Protected route – requires a valid JWT.
 */
export async function GET(request) {
  try {
    await getAuthenticatedUser(request);
    const donors = await donorService.getAllDonors();
    return NextResponse.json(donors);
  } catch (err) {
    const status = err.status || 500;
    const message = err.message || 'Internal Server Error';
    return NextResponse.json({ error: message }, { status });
  }
}

/** POST /api/donors
 * Creates a new donor record. Protected route – only authenticated staff can add donors.
 */
export async function POST(request) {
  try {
    await getAuthenticatedUser(request);
    const body = await request.json();
    const parsed = createDonorSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { error: 'Validation failed', details: parsed.error.format() },
        { status: 400 }
      );
    }
    const donor = await donorService.createDonor(parsed.data);
    return NextResponse.json(donor, { status: 201 });
  } catch (err) {
    const status = err.status || 500;
    const message = err.message || 'Internal Server Error';
    return NextResponse.json({ error: message }, { status });
  }
}
