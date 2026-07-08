import { NextResponse } from 'next/server';
import { z } from 'zod';
import { getAllDonors, createDonor } from '@/services/donorService';

// Validation schema for creating a donor
const donorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
});

/**
 * GET /api/donors
 * Returns a list of all donors.
 */
export async function GET(request) {
  try {
    const donors = await getAllDonors();
    return NextResponse.json(donors);
  } catch (error) {
    console.error('GET /api/donors error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch donors' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/donors
 * Creates a new donor record.
 */
export async function POST(request) {
  try {
    const body = await request.json();
    const parsed = donorSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json(
        {
          error: 'Invalid request data',
          details: parsed.error.format(),
        },
        { status: 400 }
      );
    }

    const newDonor = await createDonor(parsed.data);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (error) {
    console.error('POST /api/donors error:', error);
    return NextResponse.json(
      { error: 'Failed to create donor' },
      { status: 500 }
    );
  }
}
