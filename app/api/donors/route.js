import { getAllDonors, createDonor } from '../../services/donorService.js';
import { z } from 'zod';
import jwt from 'jsonwebtoken';

// Zod schema for donor creation
const donorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
});

/**
 * Verify JWT from Authorization header.
 * Throws an error if token is missing or invalid.
 */
function verifyAuth(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Missing or invalid Authorization header');
  }
  const token = authHeader.split(' ')[1];
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);
    return payload;
  } catch (err) {
    throw new Error('Invalid token');
  }
}

export async function GET(request) {
  try {
    // Ensure the request is authenticated
    verifyAuth(request);

    const donors = await getAllDonors();
    return new Response(JSON.stringify({ donors }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    const status = err.message.includes('Authorization') ? 401 : 500;
    return new Response(JSON.stringify({ error: err.message }), {
      status,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

export async function POST(request) {
  try {
    // Authentication
    verifyAuth(request);

    const body = await request.json();
    const validated = donorSchema.parse(body);

    const donor = await createDonor(validated);
    return new Response(JSON.stringify({ donor }), {
      status: 201,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    // Zod validation errors
    if (err instanceof z.ZodError) {
      return new Response(JSON.stringify({ errors: err.errors }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    const status = err.message.includes('Authorization') ? 401 : 500;
    return new Response(JSON.stringify({ error: err.message }), {
      status,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
