import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';
import { z } from 'zod';
import { getAllDonors, createDonor } from '@/services/donorService';

// Zod schema for donor creation
const donorSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email'),
  phone: z.string().optional(),
  address: z.string().optional(),
});

/**
 * Extract and verify JWT token from Authorization header.
 * Returns the decoded payload if valid, otherwise throws an error.
 */
function verifyAuth(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader) {
    throw new Error('Missing Authorization header');
  }
  const [scheme, token] = authHeader.split(' ');
  if (scheme !== 'Bearer' || !token) {
    throw new Error('Invalid Authorization format');
  }
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    return decoded;
  } catch (err) {
    throw new Error('Invalid or expired token');
  }
}

export async function GET(request) {
  try {
    // Ensure the request is authenticated (admin access)
    verifyAuth(request);

    const donors = await getAllDonors();
    return NextResponse.json(donors);
  } catch (error) {
    const status = error.message.includes('Authorization') ? 401 : 500;
    return NextResponse.json({ error: error.message }, { status });
  }
}

export async function POST(request) {
  try {
    // Authenticate admin
    verifyAuth(request);

    const body = await request.json();
    const parsed = donorSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json({ error: parsed.error.errors.map(e => e.message).join(', ') }, { status: 400 });
    }

    const newDonor = await createDonor(parsed.data);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (error) {
    const status = error.message.includes('Authorization') ? 401 : 500;
    return NextResponse.json({ error: error.message }, { status });
  }
}
