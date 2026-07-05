import { sequelize } from '../lib/db';
import { DataTypes } from 'sequelize';

// Donor model definition
// Represents an individual donor in the system.
// Fields:
//   - id: primary key
//   - firstName: donor's given name (required)
//   - lastName: donor's family name (required)
//   - email: unique contact email (required, validated as email)
//   - phone: optional contact phone number
//   - address: optional mailing address
//   - createdAt / updatedAt: timestamps managed by Sequelize

const Donor = sequelize.define(
  'Donor',
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
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
  }
);

export default Donor;
