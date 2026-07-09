import { NextResponse } from 'next/server';
import { z } from 'zod';
import donorService from '@/services/donorService';

// Zod schema for donor creation
const createDonorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
  // Additional fields can be added as needed
});

/**
 * GET /api/donors
 * Returns a list of all donors.
 */
export async function GET() {
  try {
    const donors = await donorService.getAllDonors();
    return NextResponse.json(donors);
  } catch (error) {
    console.error('Error fetching donors:', error);
    return NextResponse.json({ error: 'Failed to fetch donors' }, { status: 500 });
  }
}

/**
 * POST /api/donors
 * Creates a new donor.
 * Expected body: { name, email, phone?, address? }
 */
export async function POST(request) {
  try {
    const body = await request.json();
    const parsed = createDonorSchema.safeParse(body);

    if (!parsed.success) {
      const errors = parsed.error.errors.map((e) => ({ path: e.path, message: e.message }));
      return NextResponse.json({ error: 'Validation failed', details: errors }, { status: 400 });
    }

    const newDonor = await donorService.createDonor(parsed.data);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (error) {
    console.error('Error creating donor:', error);
    return NextResponse.json({ error: 'Failed to create donor' }, { status: 500 });
  }
}
