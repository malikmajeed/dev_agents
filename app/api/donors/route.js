import { NextResponse } from 'next/server';
import { verify } from 'jsonwebtoken';
import donorService from '../../services/donorService';
import { z } from 'zod';

// Zod schema for creating a donor
const createDonorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
});

/** Helper to extract and verify JWT token */
function getVerifiedUser(req) {
  const authHeader = req.headers.get('authorization');
  if (!authHeader) return null;
  const [scheme, token] = authHeader.split(' ');
  if (scheme !== 'Bearer' || !token) return null;
  try {
    const payload = verify(token, process.env.JWT_SECRET);
    return payload; // payload can contain user id, role, etc.
  } catch (err) {
    return null;
  }
}

export async function GET(req) {
  // Authenticate request
  const user = getVerifiedUser(req);
  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const donors = await donorService.getAllDonors();
    return NextResponse.json(donors);
  } catch (error) {
    console.error('Error fetching donors:', error);
    return NextResponse.json({ error: 'Failed to fetch donors' }, { status: 500 });
  }
}

export async function POST(req) {
  // Authenticate request
  const user = getVerifiedUser(req);
  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await req.json();
    const parsed = createDonorSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json({ error: 'Invalid request data', details: parsed.error.format() }, { status: 400 });
    }

    const newDonor = await donorService.createDonor(parsed.data);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (error) {
    console.error('Error creating donor:', error);
    return NextResponse.json({ error: 'Failed to create donor' }, { status: 500 });
  }
}
