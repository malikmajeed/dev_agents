import { DataTypes } from 'sequelize';
import db from '../lib/db.js';

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

// Associations are defined in a separate step after all models are loaded.
Donor.associate = (models) => {
  if (models.Donation) {
    Donor.hasMany(models.Donation, {
      foreignKey: 'donorId',
      as: 'donations',
    });
  }
};

export default Donor;
