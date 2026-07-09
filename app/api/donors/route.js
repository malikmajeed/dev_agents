import { getAllDonors, createDonor } from '@/services/donorService';
import jwt from 'jsonwebtoken';
import { z } from 'zod';

// Zod schema for donor creation
const donorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  amount: z.number().positive({ message: 'Amount must be positive' }),
  causeId: z.number().int().positive({ message: 'Cause ID must be a positive integer' })
});

/**
 * Verify JWT from Authorization header and return payload.
 * Throws on missing/invalid token.
 */
function verifyAuth(req) {
  const authHeader = req.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Missing or malformed Authorization header');
  }
  const token = authHeader.split(' ')[1];
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);
    return payload;
  } catch (err) {
    throw new Error('Invalid token');
  }
}

export async function GET(req) {
  try {
    // Auth check – only admins can list donors
    verifyAuth(req);

    const donors = await getAllDonors();
    return new Response(JSON.stringify(donors), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (err) {
    const status = err.message.includes('Authorization') || err.message.includes('token') ? 401 : 500;
    return new Response(JSON.stringify({ error: err.message }), {
      status,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

export async function POST(req) {
  try {
    // Auth check – only admins can create donors
    verifyAuth(req);

    const body = await req.json();
    const parsed = donorSchema.parse(body);

    const newDonor = await createDonor(parsed);
    return new Response(JSON.stringify(newDonor), {
      status: 201,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (err) {
    if (err instanceof z.ZodError) {
      return new Response(JSON.stringify({ errors: err.errors }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    const status = err.message.includes('Authorization') || err.message.includes('token') ? 401 : 500;
    return new Response(JSON.stringify({ error: err.message }), {
      status,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
