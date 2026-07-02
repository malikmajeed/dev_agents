import sequelize from '../lib/db';
import { DataTypes } from 'sequelize';

const Donor = sequelize.define('Donor', {
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

// Define associations – will be called from the central model index after all models are loaded
Donor.associate = (models) => {
  if (models.Donation) {
    Donor.hasMany(models.Donation, { foreignKey: 'donorId', as: 'donations' });
  }
};

export default Donor;
