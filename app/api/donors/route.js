import { getAllDonors, createDonor } from '@/services/donorService';
import { z } from 'zod';

// Validation schema for creating a donor
const donorCreateSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional()
});

/**
 * GET /api/donors
 * Returns a list of all donors.
 */
export async function GET(request) {
  try {
    const donors = await getAllDonors();
    return new Response(JSON.stringify({ success: true, data: donors }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    console.error('Error fetching donors:', error);
    return new Response(JSON.stringify({ success: false, error: 'Failed to fetch donors' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

/**
 * POST /api/donors
 * Creates a new donor record.
 * Expected JSON body: { name, email, phone?, address? }
 */
export async function POST(request) {
  try {
    const body = await request.json();
    const parsed = donorCreateSchema.safeParse(body);
    if (!parsed.success) {
      const errors = parsed.error.format();
      return new Response(JSON.stringify({ success: false, errors }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const newDonor = await createDonor(parsed.data);
    return new Response(JSON.stringify({ success: true, data: newDonor }), {
      status: 201,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    console.error('Error creating donor:', error);
    return new Response(JSON.stringify({ success: false, error: 'Failed to create donor' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
