import { DataTypes } from 'sequelize';
import db from '../lib/db.js';

const Donor = db.define('Donor', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  first_name: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  last_name: {
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
  underscored: true,
  timestamps: true,
});

// Associations can be defined in a central place after all models are loaded.
Donor.associate = (models) => {
  if (models.Donation) {
    Donor.hasMany(models.Donation, { foreignKey: 'donor_id', as: 'donations' });
  }
};

export default Donor;
