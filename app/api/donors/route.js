import { NextResponse } from 'next/server';
import { verify } from 'jsonwebtoken';
import { createDonor, getAllDonors } from '@/services/donorService';
import { z } from 'zod';

// Zod schema for donor creation
const donorSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email'),
  phone: z.string().optional(),
  address: z.string().optional(),
});

// Helper to verify JWT and extract payload
function verifyToken(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Missing or malformed Authorization header');
  }
  const token = authHeader.split(' ')[1];
  try {
    const payload = verify(token, process.env.JWT_SECRET);
    return payload;
  } catch (err) {
    throw new Error('Invalid token');
  }
}

export async function GET(request) {
  try {
    // Verify JWT (admin access required)
    verifyToken(request);

    const donors = await getAllDonors();
    return NextResponse.json({ success: true, data: donors }, { status: 200 });
  } catch (error) {
    const status = error.message.includes('Authorization') || error.message.includes('token') ? 401 : 500;
    return NextResponse.json({ success: false, error: error.message }, { status });
  }
}

export async function POST(request) {
  try {
    // Verify JWT (admin access required)
    verifyToken(request);

    const body = await request.json();
    const parsed = donorSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { success: false, error: parsed.error.errors.map(e => e.message).join(', ') },
        { status: 400 }
      );
    }

    const newDonor = await createDonor(parsed.data);
    return NextResponse.json({ success: true, data: newDonor }, { status: 201 });
  } catch (error) {
    const status = error.message.includes('Authorization') || error.message.includes('token') ? 401 : 500;
    return NextResponse.json({ success: false, error: error.message }, { status });
  }
}
