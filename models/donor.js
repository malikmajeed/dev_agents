import { DataTypes, Model } from 'sequelize';
import db from '../lib/db.js';

class Donor extends Model {
  static associate(models) {
    // One donor can have many donations
    if (models.Donation) {
      Donor.hasMany(models.Donation, { foreignKey: 'donor_id', as: 'donations' });
    }
    // Donor can be linked to many campaigns through donations (many‑to‑many)
    if (models.Campaign && models.Donation) {
      Donor.belongsToMany(models.Campaign, {
        through: models.Donation,
        foreignKey: 'donor_id',
        otherKey: 'campaign_id',
        as: 'campaigns',
      });
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
    firstName: {
      type: DataTypes.STRING,
      allowNull: false,
      validate: { notEmpty: true },
    },
    lastName: {
      type: DataTypes.STRING,
      allowNull: false,
      validate: { notEmpty: true },
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
      type: DataTypes.TEXT,
      allowNull: true,
    },
  },
  {
    sequelize: db,
    modelName: 'Donor',
    tableName: 'donors',
    timestamps: true,
    underscored: true,
  }
);

export default Donor;
