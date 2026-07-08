import { NextResponse } from 'next/server';
import * as donorService from '@/services/donorService';
import { z } from 'zod';

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
    const donors = await donorService.getAllDonors();
    return NextResponse.json(donors);
  } catch (error) {
    console.error('Error fetching donors:', error);
    return NextResponse.json(
      { error: 'Failed to fetch donors' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/donors
 * Creates a new donor record.
 * Expected body: { name, email, phone?, address? }
 */
export async function POST(request) {
  try {
    const body = await request.json();
    const validation = donorSchema.safeParse(body);

    if (!validation.success) {
      return NextResponse.json(
        {
          error: 'Invalid request data',
          details: validation.error.errors,
        },
        { status: 400 }
      );
    }

    const newDonor = await donorService.createDonor(validation.data);
    return NextResponse.json(newDonor, { status: 201 });
  } catch (error) {
    console.error('Error creating donor:', error);
    return NextResponse.json(
      { error: 'Failed to create donor' },
      { status: 500 }
    );
  }
}
