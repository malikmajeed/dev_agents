import db from '../lib/db.js';
import { DataTypes } from 'sequelize';

// Donor model definition
// Represents an individual donor with contact details.
// Associations (e.g., Donor.hasMany(Donation)) will be defined in the service layer
// once the Donation model is available.
const Donor = db.define('Donor', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  firstName: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  lastName: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  email: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: true,
    validate: {
      isEmail: true,
    },
  },
  phone: {
    type: DataTypes.STRING,
    allowNull: true,
  },
  address: {
    type: DataTypes.TEXT,
    allowNull: true,
  },
}, {
  tableName: 'donors',
  timestamps: true,
});

export default Donor;
