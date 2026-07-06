import db from '../lib/db.js';
import { DataTypes } from 'sequelize';

// Donor model definition
const Donor = db.define(
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
    // Store bcrypt hash of the password; actual hashing is handled in services
    passwordHash: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    // Optional fields for future extensions
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
    // Ensure the model name is singular for association clarity
    modelName: 'Donor',
  }
);

// Associations – will be called from a central association loader after all models are imported
Donor.associate = (models) => {
  // A donor can have many donation records (Donation model to be created later)
  if (models.Donation) {
    Donor.hasMany(models.Donation, { foreignKey: 'donorId', as: 'donations' });
  }
};

export default Donor;
