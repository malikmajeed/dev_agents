import { DataTypes } from 'sequelize';
import sequelize from '../lib/db.js';

// Donor model definition
// Represents an individual who can make donations. Includes basic contact
// information and a hashed password for authentication (if needed).
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
      validate: { isEmail: true },
    },
    // Store bcrypt hash of the donor's password (if donors log in).
    passwordHash: {
      type: DataTypes.STRING,
      allowNull: false,
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
    // Ensure the model uses underscored column names to match typical DB style.
    underscored: true,
  }
);

// Associations can be defined later after all models are loaded.
// Example (when a Donation model exists):
// Donor.hasMany(models.Donation, { foreignKey: 'donor_id', as: 'donations' });

export default Donor;
