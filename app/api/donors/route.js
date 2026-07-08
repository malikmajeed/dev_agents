import { getAllDonors, createDonor } from '@/services/donorService';
import { z } from 'zod';
import jwt from 'jsonwebtoken';

// Zod schema for donor creation – adjust fields as the model evolves
const donorCreateSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional()
});

// Helper to verify JWT – throws if invalid
function verifyToken(token) {
  const secret = process.env.JWT_SECRET;
  if (!secret) {
    throw new Error('JWT_SECRET is not defined in environment');
  }
  return jwt.verify(token, secret);
}

/**
 * GET /api/donors
 * Returns a list of all donors.
 */
export async function GET(request) {
  try {
    // Optional auth – admins only. If you want public access, remove this block.
    const authHeader = request.headers.get('authorization');
    if (authHeader?.startsWith('Bearer ')) {
      const token = authHeader.split(' ')[1];
      verifyToken(token);
    }

    const donors = await getAllDonors();
    return new Response(JSON.stringify({ success: true, data: donors }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    console.error('GET /api/donors error:', error);
    return new Response(JSON.stringify({ success: false, error: error.message }), {
      status: error.name === 'JsonWebTokenError' ? 401 : 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

/**
 * POST /api/donors
 * Creates a new donor record.
 */
export async function POST(request) {
  try {
    const authHeader = request.headers.get('authorization');
    if (!authHeader?.startsWith('Bearer ')) {
      return new Response(JSON.stringify({ success: false, error: 'Missing Authorization header' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    const token = authHeader.split(' ')[1];
    verifyToken(token);

    const body = await request.json();
    const parsed = donorCreateSchema.safeParse(body);
    if (!parsed.success) {
      const errors = parsed.error.format();
      return new Response(JSON.stringify({ success: false, error: 'Validation failed', details: errors }), {
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
    console.error('POST /api/donors error:', error);
    const status = error.name === 'JsonWebTokenError' ? 401 : 500;
    return new Response(JSON.stringify({ success: false, error: error.message }), {
      status,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
