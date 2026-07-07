import { DataTypes } from 'sequelize';
import { sequelize } from '../lib/db.js';

// Donor model definition
// Represents an individual who can make donations to the NGO.
// Fields include basic contact information and timestamps.

const Donor = sequelize.define(
  'Donor',
  {
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
  },
  {
    tableName: 'donors',
    timestamps: true,
    underscored: true,
  }
);

// Define associations in a separate init step to avoid circular dependencies.
// Example (when a Donation model exists):
// Donor.hasMany(models.Donation, { foreignKey: 'donor_id', as: 'donations' });

export default Donor;
