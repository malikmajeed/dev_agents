import { DataTypes, Model } from 'sequelize';
import sequelize from '../lib/db.js';

class Donor extends Model {
  static associate(models) {
    // A donor can have many donations
    if (models.Donation) {
      this.hasMany(models.Donation, { foreignKey: 'donor_id', as: 'donations' });
    }
  }
}

Donor.init(
  {
    id: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      primaryKey: true,
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
  },
  {
    sequelize,
    modelName: 'Donor',
    tableName: 'donors',
    timestamps: true,
    underscored: true,
  }
);

export default Donor;
