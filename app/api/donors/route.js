import { NextResponse } from 'next/server';
import { verify } from 'jsonwebtoken';
import { createDonor, getAllDonors } from '../../../../../services/donorService.js';
import { z } from 'zod';

// Zod schema for donor creation
const donorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
});

/**
 * Helper to verify JWT token from Authorization header.
 * Returns the decoded payload if valid, otherwise null.
 */
async function authenticate(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader) return null;
  const parts = authHeader.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') return null;
  const token = parts[1];
  try {
    const payload = verify(token, process.env.JWT_SECRET);
    return payload;
  } catch (err) {
    return null;
  }
}

export async function GET(request) {
  const user = await authenticate(request);
  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const donors = await getAllDonors();
    return NextResponse.json(donors, { status: 200 });
  } catch (error) {
    console.error('Error fetching donors:', error);
    return NextResponse.json({ error: 'Failed to fetch donors' }, { status: 500 });
  }
}

export async function POST(request) {
  // Public donation page may allow unauthenticated creation; adjust as needed.
  // If you want to enforce auth, uncomment the lines below.
  // const user = await authenticate(request);
  // if (!user) {
  //   return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  // }

  try {
    const body = await request.json();
    const parsed = donorSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json({ error: 'Invalid input', details: parsed.error.format() }, { status: 400 });
    }

    const newDonor = await createDonor(parsed.data);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (error) {
    console.error('Error creating donor:', error);
    return NextResponse.json({ error: 'Failed to create donor' }, { status: 500 });
  }
}
