import { DataTypes } from 'sequelize';
import db from '../lib/db.js';

// Define the Donor model
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
    validate: { isEmail: true },
  },
  phone: {
    type: DataTypes.STRING,
    allowNull: true,
  },
  address: {
    type: DataTypes.STRING,
    allowNull: true,
  },
  city: {
    type: DataTypes.STRING,
    allowNull: true,
  },
  state: {
    type: DataTypes.STRING,
    allowNull: true,
  },
  zip: {
    type: DataTypes.STRING,
    allowNull: true,
  },
}, {
  tableName: 'donors',
  timestamps: true,
});

// Associations – will be called from a central model index after all models are loaded
Donor.associate = (models) => {
  if (models.Donation) {
    Donor.hasMany(models.Donation, { foreignKey: 'donorId', as: 'donations' });
  }
};

export default Donor;
