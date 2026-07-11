import { NextResponse } from 'next/server';
import { verify } from 'jsonwebtoken';
import { z } from 'zod';
import donorService from '@/services/donorService';

// Validation schema for creating a donor
const createDonorSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  phone: z.string().optional(),
  address: z.string().optional(),
  // password is stored hashed; donors may have an account
  password: z.string().min(6).optional(),
});

// Helper to verify JWT and extract payload
function verifyAuth(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null;
  }
  const token = authHeader.split(' ')[1];
  try {
    const payload = verify(token, process.env.JWT_SECRET);
    return payload;
  } catch (err) {
    return null;
  }
}

export async function GET(request) {
  // Only admins can list donors; verify token
  const user = verifyAuth(request);
  if (!user || !user.role || user.role !== 'admin') {
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

export async function POST(request) {
  // Only admins can create donors; verify token
  const user = verifyAuth(request);
  if (!user || !user.role || user.role !== 'admin') {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await request.json();
    const parsed = createDonorSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json({ error: 'Invalid request body', details: parsed.error.format() }, { status: 400 });
    }
    const newDonor = await donorService.createDonor(parsed.data);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (error) {
    console.error('Error creating donor:', error);
    return NextResponse.json({ error: 'Failed to create donor' }, { status: 500 });
  }
}
